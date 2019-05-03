#!/usr/bin/env python
'''
Code Speak Labs: Congressional App Challenge Demo
'''

import os
from json import load, dump
from flask import Flask, render_template, request, redirect, url_for
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

__author__ = "Karen Vu"
__email__ = "karenkv@uci.edu"

app = Flask(__name__)  #Global variable to run app with Flask

username = "" #Global variable to track who current user is


@app.route("/", methods=["GET"])
def main():
    '''
    Renders the intial web application page
    '''
    if "message" in request.args: #Checks if there's a message attached to URL and if so will return that message when rendering template to be formatted into an alert.
        login_message = request.args["message"]
        return render_template("index.html", message=login_message)
    return render_template("index.html")


@app.route("/home-page", methods=["GET"])
def home_page():
    '''
    Renders the home page after successful login or account creation
    '''
    if "message" in request.args: #Checks if there's a message attached to URL and if so will return that message when rendering template to be formatted into an alert.
        create_message = request.args["message"]
        create_content = chatlog_helper()
        return render_template("home-page.html", message=create_message, content=create_content)
    if "content" in request.args: #Checks if there's a content attached to URL and if so will return that content when rendering template to be formatted into an alert.
        create_content = request.args["content"]
        return render_template("home-page.html", content = create_content)
    return render_template("home-page.html")


@app.route("/handle-login", methods=["POST"])
def handle_login():
    '''
    Handles the user login by checking the input against the logins database to see if:
    1) Username exists and 
    2) Username and password combination exists
    If both items are fulfilled, redirects to home page. Otherwise redirects to main page with message response.
    '''
    if request.method == "POST":
        global username
        username = request.form["username"]
        password = request.form["password"]
        with open("login.json", "r") as f:
            login_creds = load(f)
        try:
            real_password = login_creds[username]["password"]
        except KeyError: #Handles if username does not exist.
            return redirect(
                url_for(
                    "main",
                    message=
                    "Please enter a valid username and password combination."))
        else:
            if password == real_password:
                return redirect(url_for("home_page", message="Login success!", content=chatlog_helper()))
            else: #Handles if password matches username
                return redirect(
                    url_for(
                        "main",
                        message=
                        "Please enter a valid username and password combination."
                    ))


@app.route("/handle-create", methods=["POST"])
def handle_create():
    '''
    Handles account creation by taking input and writing to JSON file and sending email via SendGrid

    Note: With Repl.it's IDE, any updates made to the files in the filesystem directly won’t show up in the editor. However, the code is still correct and can be checked with print statements in the console. With every account creation, the refresh command in the console must be run to pick up the changes. There is currently no work around when application is ran through Repl.it's IDE.
    '''
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        school = request.form["school"]
        email = request.form["email"]
        with open("login.json", "r") as f: #Loads data from JSON
            data = load(f)
            print(data)
        #Manipulates the data
        data[username] = {
            "password": password,
            "school": school,
            "email": email
        }
        with open("login.json", "w") as f: #Updates data in JSON
            dump(data, f, indent=2)
            print(data)
        handle_sg("donotreply@happyplace.com", email, "Welcome to HappyPlace!", "Username: " + username + "\nPassword: " + password)
        return redirect(
            url_for(
                "home_page",
                message=
                "Account created successfully! Please check your email for your login information.",  content=chatlog_helper()
            ))


@app.route("/handle-contact", methods=["POST"])
def handle_contact():
    '''
    Handles contact form submission by taking request inputs and piping to SendGrid helper
    '''
    from_name = request.form["name"]
    from_email = request.form["email"]
    subject = request.form["subject"]
    message = request.form["message"]
    with open("login.json", "r") as f:
        user_data = load(f)
    school = user_data[username]["school"]
    with open("counselors.json", "r") as f:
        counselor_data = load(f)
    to_name = counselor_data[school]["name"]
    to_email = counselor_data[school]["email"]
    handle_sg(from_email, to_email, subject, "Hello " + to_name + ",\n" + message + "\nBest,\n"+from_name)
    return redirect(url_for("home_page", message="Message sent successfully!", content=chatlog_helper()))


@app.route("/handle-chat", methods=["POST"])
def handle_chat():
    '''
    Handles chat requests by reading and writing to the chatlog JSON file
    '''
    message = request.form["message"]
    with open("chatlog.json", "r") as f:
        data = load(f)
    num = len(data.keys()) + 1
    data[num] = {"username": username,"message": message}
    with open("chatlog.json", "w") as f:
        dump(data, f, indent=2)
    content = chatlog_helper()
    return redirect(url_for("home_page", content=content))
    
 
def chatlog_helper():
    '''
    Formats the messageboard by reading in chatlog and user data accordingly
    '''
    with open("chatlog.json", "r") as f:
        data = load(f)
    with open("login.json", "r") as f:
        user_data = load(f)
    content = ""
    for k,v in data.items():
        content += "<b>" + v["username"] + "</b> (" + user_data[v["username"]]["school"] + "): " + v["message"] + "</br>"
    return content


def handle_sg(from_: str, to_: str, subj: str, content: str) -> None:
    '''
    Handles emailing through SendGrid API
    '''
    message = Mail(
        from_email= from_,
        to_emails= to_,
        subject=subj,
        html_content=content)
    sg = SendGridAPIClient(os.environ.get('SGAPIKEY'))
    response = sg.send(message)
  

if __name__ == '__main__':  #Run app with specified host
    app.run(host='0.0.0.0', port=5000)
