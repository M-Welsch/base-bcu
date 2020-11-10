from flask import Flask, redirect, url_for
app = Flask(__name__)

@app.route('/admin')
def hello_admin():
	return 'Hello Admin!'

@app.route('/guest/<name_of_guest>')
def hello_guest(name_of_guest):
	return 'Hello %s, my guest!' % name_of_guest


@app.route('/user/<name>')
def hello_world(name):
	if name == 'admin':
		return redirect(url_for('hello_admin'))
	else:
		return redirect(url_for('hello_guest', name_of_guest=name))

if __name__ == '__main__':
   app.run(debug=True)