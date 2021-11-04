from pymongo import MongoClient
import jwt
import datetime
import hashlib
from flask import Flask, render_template, jsonify, request, redirect, url_for
from datetime import datetime, timedelta

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['UPLOAD_FOLDER'] = "./static/profile_pics"

SECRET_KEY = 'SPARTA'


client = MongoClient('localhost', 27017)
db = client.dbteamsparta


# 메인화면 렌더링
@app.route('/')
def home():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])

        return render_template('login.html')
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))


@app.route('/login')
def login():
    msg = request.args.get("msg")
    return render_template('login.html', msg=msg)


@app.route('/sign_in', methods=['POST'])
def sign_in():
    # 로그인
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']

    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    result = db.users.find_one({'username': username_receive, 'password': pw_hash})

    if result is not None:
        payload = {
         'id': username_receive,
         'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)  # 로그인 24시간 유지
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256').decode('utf-8')

        return jsonify({'result': 'success', 'token': token})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})


@app.route('/sign_up/save', methods=['POST'])
def sign_up():
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    doc = {
        "username": username_receive,                               # 아이디
        "password": password_hash,                                  # 비밀번호
        "profile_name": username_receive,                           # 프로필 이름 기본값은 아이디
        "profile_pic": "",                                          # 프로필 사진 파일 이름
        "profile_pic_real": "profile_pics/profile_placeholder.png", # 프로필 사진 기본 이미지
        "profile_info": ""                                          # 프로필 한 마디
    }
    db.users.insert_one(doc)
    return jsonify({'result': 'success'})


# 아이디 중복확인 서버부분
@app.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    username_receive = request.form['username_give']
    exists = bool(db.users.find_one({"username": username_receive}))
    return jsonify({'result': 'success', 'exists': exists})


# 회원 정보 저장

@app.route('/api/Register', methods=['POST'])
def register_create():
    regUserName_receive = request.form["regUserName_give"]
    regPassword_receive = request.form["regPassword_give"]

    doc = {
        "regUserName": regUserName_receive,
        "regPassword": regPassword_receive
    }
    db.Register.insert_one(doc)

    return jsonify({'result': 'success', 'msg': '화원정보가 저장됨'})


# 선택화면 렌더링
@app.route('/line', methods=['GET'])
def line():
    a = []
    stations = []
    shop = list(db.restaurant.find({}, {'_id': False}))
    for re in shop:
        a.append(re['place'])
    for re in a:
        if re not in stations:
            stations.append(re)
    return render_template('line_choice.html', stations=stations)


# 리뷰 페이지
@app.route('/review/<keyword>', methods=['GET'])
def review(keyword):
    shop = db.restaurant.find_one({"name": keyword}, {"_id": False})
    review = list(db.restaurant_review.find({"shop": keyword}, {"_id": False}))
    place = list(db.restaurant.find({}, {'_id': False}))

    a = []
    stations = []

    for re in place:
        a.append(re['place'])
    for re in a:
        if re not in stations:
            stations.append(re)

    return render_template('review.html', shop=shop, word=keyword, review=review, stations=stations)


# line_base.html
# 로고 클릭시 전부 송출
@app.route('/shop', methods=['GET'])
def all():
    app.jinja_env.add_extension('jinja2.ext.loopcontrols')
    array = []
    stations = []
    shop = list(db.restaurant.find({}, {'_id': False}).sort('like', -1))
    titles = list(db.restaurant_review.find({}, {"_id": False}))

    for re in shop:
        array.append(re['place'])
    for re in array:
        if re not in stations:
            stations.append(re)
    title = []
    length = len(titles)
    for i in range(length - 1, -1, -1):
        title.append(titles[i])

    return render_template('line_base.html', shop=shop, title=title, stations=stations)


# 각 역 클릭시 해당 역 식당 리스트업
@app.route('/shop/<keyword2>', methods=['GET'])
def line1(keyword2):
    app.jinja_env.add_extension('jinja2.ext.loopcontrols')
    array = []
    stations = []
    station = list(db.restaurant.find({}, {'_id': False}))
    titles = list(db.restaurant_review.find({}, {"_id": False}))
    for re in station:
        array.append(re['place'])
    for re in array:
        if re not in stations:
            stations.append(re)
    title = []
    length = len(titles)
    for i in range(length-1, -1, -1):
        title.append(titles[i])
    shop = list(db.restaurant.find({'place': keyword2}).sort('like', -1))
    return render_template('line_base.html', shop=shop, title=title, stations=stations)


# 평점0점 초기화
# db.restaurant.update_many({},{'$set':{'like':0}})


# 리뷰작성
@app.route('/api/review_create', methods=['POST'])
def review_create():
    shop_receive = request.form["shop_give"]
    score_receive = request.form["score_give"]
    reviews_receive = request.form["reviews_give"]
    date_receive = request.form["date_give"]
    img_receive = request.form["img_give"]

    doc = {
        "reviews": reviews_receive,
        "score": score_receive,
        "shop": shop_receive,
        "date": date_receive,
        "img": img_receive
    }

    db.restaurant_review.insert_one(doc)
    db.restaurant.update_one({'name': shop_receive}, {'$set': {'like': int(score_receive)}})

    return jsonify({'result': 'success', 'msg': '리뷰가 저장 되었습니다!!'})





# 리뷰 보기
@app.route('/my/reviews', methods=['GET'])
def review_show():
    my_reviews = list(db.restaurant_review.find({}, {"_id": False}))
    return render_template('myReview.html', review=my_reviews)


# 리뷰 수정
@app.route('/my/review/modify', methods=['POST'])
def review_modify():
    review_desc = request.form["review_desc"]
    review_name = request.form["review_name"]
    db.restaurant_review.update_one({'shop': review_name}, {'$set': {'reviews': review_desc}})
    return jsonify({'msg': '수정이 완료되었습니다!'})


# 리뷰 제거
@app.route('/my/review/delete', methods=['POST'])
def review_delete():
    review_name = request.form["review_name"]
    review_Length = list(db.restaurant_review.find({"shop":review_name}))
    if len(review_Length) == 1:
        db.restaurant.update_one({"name": review_name}, {'$set': {'like': 0}})
    review_desc = request.form["review_desc"]
    db.restaurant_review.delete_one({'shop': review_name, 'reviews': review_desc})
    # db.restaurant.update_many({},{'$set':{'like':0}})
    return jsonify({'msg': '삭제가 완료되었습니다!'})


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
