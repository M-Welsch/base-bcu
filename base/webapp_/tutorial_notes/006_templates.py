from flask import Flask, render_template
app = Flask(__name__)

@app.route('/hello/<user>')
def hello_name(user):
   return render_template('006_hello.html', name = user, user_index = 6)

if __name__ == '__main__':
   app.run(debug = True)