from flask import Flask
app = Flask(__name__)

@app.route('/<name>')
def hello_world(name):
   return 'Hello %s!' % name

@app.route('/cakes/<int:number>')
def cakes(number):
	return 'Public cake number %i' % number

if __name__ == '__main__':
   app.run(debug=True)