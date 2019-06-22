from cloudant import Cloudant
from flask import Flask, render_template, request, jsonify
import atexit
import os
import json
from watson_developer_cloud import VisualRecognitionV3, \
    WatsonApiException
#
{
  "visualRecognition": [
    {
      "name": "my-app-easiy-visualrecogniti-1560073279526",
      "credentials": {
        "apikey": "b09m0bUeSsQq-X4D6TeuFTMqRpr3Jx85itK4FRQU15ca",
        "url": "https://gateway.watsonplatform.net/visual-recognition/api"
      }
    }
  ]
}
#

app = Flask(__name__, static_url_path='')

db_name = 'mydb'
client = None
db = None

if 'VCAP_SERVICES' in os.environ:
    vcap = json.loads(os.getenv('VCAP_SERVICES'))
    print('Found VCAP_SERVICES')
    if 'cloudantNoSQLDB' in vcap:
        creds = vcap['cloudantNoSQLDB'][0]['credentials']
        user = creds['username']
        password = creds['password']
        url = 'https://' + creds['host']
        client = Cloudant(user, password, url=url, connect=True)
        db = client.create_database(db_name, throw_on_exists=False)
elif "CLOUDANT_URL" in os.environ:
    client = Cloudant(os.environ['CLOUDANT_USERNAME'], os.environ['CLOUDANT_PASSWORD'], url=os.environ['CLOUDANT_URL'], connect=True)
    db = client.create_database(db_name, throw_on_exists=False)
elif os.path.isfile('vcap-local.json'):
    with open('vcap-local.json') as f:
        vcap = json.load(f)
        print('Found local VCAP_SERVICES')
        creds = vcap['services']['cloudantNoSQLDB'][0]['credentials']
        user = creds['username']
        password = creds['password']
        url = 'https://' + creds['host']
        client = Cloudant(user, password, url=url, connect=True)
        db = client.create_database(db_name, throw_on_exists=False)

# On IBM Cloud Cloud Foundry, get the port number from the environment variable PORT
# When running this app on the local machine, default the port to 8000
port = int(os.getenv('PORT', 8000))

@app.route('/')
def root():
    return app.send_static_file('index.html')


@atexit.register
def shutdown():
    if client:
        client.disconnect()


@app.route('/api/visual_recognition', methods=['POST'])
def visual_recognition():
    file = request.files['img_file']
    filename = file.filename.split('.')[0] + '_new.' + file.filename.split('.')[-1]
    dir_path = os.path.dirname(os.path.realpath(__file__))
    # print(dir_path)
    img_dir = dir_path + '/static/img/'
    path = img_dir + filename

    for the_file in os.listdir(img_dir):
        file_path = os.path.join(img_dir, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            # elif os.path.isdir(file_path): shutil.rmtree(file_path)
        except Exception as e:
            print(e)

    print
    file.filename, filename, path
    file.save(path)
    print
    'GET=', file.filename
    print
    'UPLOAD=', filename, '#' * 50
    # return jsonify({"result": path})

    visual_recognition = VisualRecognitionV3(
        '2018-03-19',
        iam_apikey='b09m0bUeSsQq-X4D6TeuFTMqRpr3Jx85itK4FRQU15ca')

    with open(path, 'rb') as images_file:
        faces = visual_recognition.detect_faces(images_file).get_result()
    # # # print(json.dumps(faces, indent=2))
    # # return json.dumps({"result": faces})
    result = json.loads(json.dumps(faces, indent=2))

    persons = []
    for img in result["images"]:
        for face in img["faces"]:
            min_age = face["age"]["min"]
            max_age = face["age"]["max"]
            age = str(min_age) + ' - ' + str(max_age)
            gender = face["gender"]["gender"]
            person = ["Age: " + str(age), "Gender: " + str(gender)]
            persons.append(person)

    result = {"result": persons}

    return jsonify(result)
    # return jsonify({"result": result})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port, debug=True)

