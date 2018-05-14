from flask import Flask, render_template

app = Flask(__name__)

# @app.route('/', methods=['GET', 'HEAD'])
# def front_page():
#     return render_template('front_page.html', urim=urim)

@app.route('/socialcard/<path:uri>', methods=['GET', 'HEAD'])
def make_social_card(uri=None):
    return render_template('social_card.html', urim=uri)


# if __name__ == '__main__':
#     app.run()