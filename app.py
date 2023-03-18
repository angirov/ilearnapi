import os.path
import os
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from flask_mail import Mail, Message

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = \
    "sqlite:///" + os.path.join(basedir, "planets.db")
app.config["JWT_SECRET_KEY"] = 'SECRET'
app.config["MAIL_SERVER"] = 'sandbox.smtp.mailtrap.io'
app.config["MAIL_USERNAME"] = os.environ['MAIL_USERNAME']
app.config["MAIL_PASSWORD"] = os.environ['MAIL_PASSWORD']

db = SQLAlchemy(app)
ma = Marshmallow(app)
jwt = JWTManager(app)
mail = Mail(app)


@app.cli.command("db_create")
def db_creat():
    db.create_all()
    print("Database created")

@app.cli.command("db_drop")
def db_drop():
    db.drop_all()
    print("Database dropped")

@app.cli.command("db_seed")
def seed():
    mercury = Planet(
        planet_type = "Class D",
        planet_name = "Mercury",
        home_star = "Sol",
        mass = 3.258e23,
        radius = 1516,
        distance = 35.98e6)
    venus = Planet(
        planet_type="Class K",
        planet_name="Venus",
        home_star="Sol",
        mass=4.86,
        radius=3760,
        distance=67.24e6)
    earth = Planet(
        planet_type="Class M",
        planet_name="Earth",
        home_star="Sol",
        mass=5.972e24,
        radius=3969,
        distance=92.24e6)
    db.session.add(mercury)
    db.session.add(venus)
    db.session.add(earth)

    test_user = User(
        first_name='Harry',
        last_name='Potter',
        email='test@test.com',
        password='pw'
    )
    db.session.add(test_user)
    db.session.commit()
    print("Database seeded!")


@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'


@app.route('/super-simple')
def super_simple():  # put application's code here
    return jsonify(message='super simple')


@app.route('/not-found')
def not_found():
    return jsonify(message="NOT FOUND"), 404


@app.route('/parameters')
def parameters():
    name = request.args.get('name')
    age = request.args.get('age')
    return age_check(name, age)


def age_check(name, age):
    if int(age) < 18:
        return jsonify(message=f"Sorry {name}, you are not old enough!"), 401
    else:
        return jsonify(message=f"Wellcome {name}!")


@app.route('/url_vars/<string:name>/<int:age>')
def url_vars(name: str, age: int):
    return age_check(name, age)


@app.route('/planets', methods=['GET'])
def planets():
    planet_list = Planet.query.all()
    results = planets_schema.dump(planet_list)
    return jsonify(results)


@app.route('/planet_details/<planet_id>', methods=['GET'])
def planet_details(planet_id):
    planet = Planet.query.filter_by(planet_id=planet_id).first()
    if planet:
        results = planet_schema.dump(planet)
        return jsonify(results)
    else:
        return jsonify(message="Planet not found!")


@app.route('/add_planet', methods=['POST'])
@jwt_required()
def add_planet():
    if request.is_json:
        planet_type = request.json['planet_type']
        planet_name = request.json['planet_name']
        home_star = request.json['home_star']
        mass = request.json['mass']
        radius = request.json['radius']
        distance = request.json['distance']
    else:
        planet_type = request.form['planet_type']
        planet_name = request.form['planet_name']
        home_star = request.form['home_star']
        mass = request.form['mass']
        radius = request.form['radius']
        distance = request.form['distance']
    planet = Planet.query.filter_by(planet_name=planet_name).first()
    if planet:
        return jsonify(
            message=f"Planet {planet_name} already registered"
        )
    else:
        planet = Planet(
            planet_type=planet_type,
            planet_name=planet_name,
            home_star=home_star,
            mass=float(mass),
            radius=float(radius),
            distance=float(distance)
        )
        db.session.add(planet)
        db.session.commit()
        return jsonify(
            message=f'New planet {planet_name} has been registered!'
        )


@app.route('/update_planet/<int:planet_id>', methods=['PUT'])
@jwt_required()
def update_planet(planet_id):
    planet_id = int(planet_id)
    if request.is_json:
        planet_type = request.json['planet_type']
        planet_name = request.json['planet_name']
        home_star = request.json['home_star']
        mass = request.json['mass']
        radius = request.json['radius']
        distance = request.json['distance']
    else:
        planet_type = request.form['planet_type']
        planet_name = request.form['planet_name']
        home_star = request.form['home_star']
        mass = request.form['mass']
        radius = request.form['radius']
        distance = request.form['distance']
    planet = Planet.query.filter_by(planet_id=planet_id).first()
    if planet:
        planet.planet_type = planet_type
        planet.planet_name = planet_name
        planet.home_star = home_star
        planet.mass = float(mass)
        planet.radius = float(radius)
        planet.distance = float(distance)
        db.session.commit()
        return jsonify(message=f'Planet {planet_name} has been undated!'), 202

    else:
        return jsonify(message=f'Planet #{planet_id} not registered!')


@app.route('/delete_planet/<int:planet_id>', methods=['DELETE'])
@jwt_required()
def delete_planet(planet_id: int):
    planet = Planet.query.filter_by(planet_id=planet_id).first()
    if planet:
        db.session.delete(planet)
        db.session.commit()
        return jsonify(message=f'Planet {planet_id} has been deleted!'), 202
    else:
        return jsonify(message=f'Planet #{planet_id} not registered!')


@app.route('/register', methods=['POST'])
def register():
    email = request.form['email']
    test = User.query.filter_by(email=email).first()
    if test:
        return jsonify(message="This email is already registered."), 409
    else:
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']
        user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password
        )
        db.session.add(user)
        db.session.commit()
        return jsonify(message="User created successfully"), 201


@app.route('/login', methods=['POST'])
def login():
    if request.is_json:
        email = request.json['email']
        password = request.json['password']
    else:
        email = request.form['email']
        password = request.form['password']
    test = User.query.filter_by(email=email, password=password).first()
    if test:
        access_token = create_access_token(identity=email)
        return jsonify(message="Login sussesful!", access_token=access_token)
    else:
        return jsonify(message="Bad login or password"), 401


@app.route('/retrieve_password/<string:email>', methods=["GET"])
def retrieve_password(email):
    user = User.query.filter_by(email=email).first()
    if user:
        msg = Message("your planetary API password is " + user.password,
                      sender="admin@planerary.com",
                      recipients=[email])
        mail.send(msg)
        return jsonify(message="Password sent")
    else:
        return jsonify(message="Email not found")


# database models
class User(db.Model):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)


class Planet(db.Model):
    __tablename__ = "planets"
    planet_id = Column(Integer, primary_key=True)
    planet_type = Column(String)
    planet_name = Column(String)
    home_star = Column(String)
    mass = Column(Float)
    radius = Column(Float)
    distance = Column(Float)


class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'first_name', 'last_name', 'email', 'password')


class PlanetSchema(ma.Schema):
    class Meta:
        fields = ('planet_id', 'planet_type', 'planet_name', 'home_star', 'mass', 'radius', 'distance')


user_schema = UserSchema()
users_schema = UserSchema(many=True)

planet_schema = PlanetSchema()
planets_schema = PlanetSchema(many=True)

if __name__ == '__main__':
    app.run()
