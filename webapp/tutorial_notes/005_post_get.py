from flask import Flask, redirect, url_for, request
app = Flask(__name__)

@app.route('/success/<date_to_display>')
def success(date_to_display):
   return 'the date: %s' % date_to_display

@app.route('/005_login',methods = ['POST', 'GET'])
def login():
   if request.method == 'POST':
      my_date = request.form['date_from_form']
      my_text = request.form['nm'] #unused
      return redirect(url_for('success',date_to_display = my_date))
   else:
      my_date = request.args.get('date_from_form')
      my_text = request.args.get('nm') #unused
      return redirect(url_for('success',date_to_display = my_date))

if __name__ == '__main__':
   app.run(debug = True)