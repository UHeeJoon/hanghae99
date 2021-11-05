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


## 로그인 페이지
@app.route('/login')
def login():
    msg = request.args.get("msg")
    return render_template('login.html', msg=msg)


## 로그인 api
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
        "username": username_receive,  # 아이디
        "password": password_hash,  # 비밀번호
        "profile_name": username_receive,  # 프로필 이름 기본값은 아이디
        "profile_pic": "",  # 프로필 사진 파일 이름
        "profile_pic_real": "profile_pics/profile_placeholder.png",  # 프로필 사진 기본 이미지
        "profile_info": ""  # 프로필 한 마디
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
    regUserName_receive = request.form["regUserName_give"]  # 받아온 아이디
    regPassword_receive = request.form["regPassword_give"]  # 받아온 비밀번호

    doc = {
        "regUserName": regUserName_receive,  # 아이디
        "regPassword": regPassword_receive  # 비밀번호
    }
    db.Register.insert_one(doc)     # db에 사용자 정보 저장

    return jsonify({'result': 'success', 'msg': '화원정보가 저장됨'})


# 선택화면 렌더링
@app.route('/line', methods=['GET'])
def line():
    # 지동 로그아웃////////////////////////////////////////////////////////////////
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])

    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))
    # /////////////////////////////////////////////////////////////////////////

    a = []
    stations = []
    shop = list(db.restaurant.find({}, {'_id': False}))
    for re in shop:
        a.append(re['place'])
    for re in a:
        if re not in stations:
            stations.append(re)
    return render_template('line_choice.html', stations=stations)


# line_base.html
# 로고 클릭시 전부 송출

@app.route('/shop', methods=['GET'])
def all():
    # 지동 로그아웃////////////////////////////////////////////////////////////////
    app.jinja_env.add_extension('jinja2.ext.loopcontrols')
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])

    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))
    # ///////////////////////////////////////////////////////////////////////////

    shop = list(db.restaurant.find({}, {'_id': False}).sort('like', -1))    # 모든 식당 정보 like가 많은 순으로 shop[] 생성
    titles = list(db.restaurant_review.find({}, {"_id": False}))            # 모든 리뷰 정보 title[]에 생성

    array = []
    for sh in shop:
        array.append(sh['place'])       # 모든 전철역 array[]에 .append

    stations = []
    for ar in array:
        if ar not in stations:
            stations.append(ar)         # 중복을 제거한 모든 전철역 station[]에 .append

    title = []
    length = len(titles)
    for i in range(length - 1, -1, -1):
        title.append(titles[i])     # 리뷰 역 정렬

    # 리뷰 점수 업데이트
    for sh in shop:
        allScore = list(db.restaurant_review.find({'shop': sh['name']}))    # 해당 식당에 해당하는 리뷰 정보 allScore[] 생성
        point = []
        if not allScore:        # 해당 식당에 리뷰가 없으면 평점 0으로 초기화
            average = 0
        else:                   # 해당 식당에 리뷰가 있으면 (총 별점의 합/ 리뷰의 개수)으로 평점 average 생성
            for score in allScore:
                point.append(score['score'])
                intPoint = list(map(int, point))
                sumPoint = sum(intPoint)
            result = sumPoint / len(point)
            average = f'{result: .1f}'
        db.restaurant.update_one({'name': sh['name']}, {'$set': {'like': average}})     # 해당 식당 db에 average 업데이트

    return render_template('line_base.html', shop=shop, title=title, stations=stations)


# 각 역 클릭시 해당 역 식당 리스트업
@app.route('/shop/<keyword2>', methods=['GET'])
def line1(keyword2):
    # 지동 로그아웃////////////////////////////////////////////////////////////////
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])

    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))
    # /////////////////////////////////////////////////////////////////////////////

    app.jinja_env.add_extension('jinja2.ext.loopcontrols')          # jinja에 break를 쓰기위한 코드
    station = list(db.restaurant.find({}, {'_id': False}))          # 모든 데이터 호출 station에 저장
    titles = list(db.restaurant_review.find({}, {"_id": False}))    # 모든 리뷰 데이터 호출 titles에 저장

    array = []
    for re in station:
        array.append(re['place'])   # 모든 전철역 array[]에 .append

    stations = []
    for re in array:
        if re not in stations:
            stations.append(re)     # 중복을 제거한 모든 전철역 station[]에 .append

    title = []
    length = len(titles)
    for i in range(length - 1, -1, -1):
        title.append(titles[i])     # 리뷰 역 정렬

    shop = list(db.restaurant.find({'place': keyword2}).sort('like', -1))       # like 역순으로 모든 식당 데이터 shop[]에 생성
    # 리뷰 점수 업데이트
    for sh in shop:
        allScore = list(db.restaurant_review.find({'shop': sh['name']}))        # 해당 식당에 해당하는 리뷰 정보 allScore[] 생성
        point = []
        if not allScore:
            average = 0         # 해당 식당에 리뷰가 없으면 평점 0으로 초기화
        else:
            for score in allScore:      # 해당 식당에 리뷰가 있으면 (총 별점의 합/ 리뷰의 개수)으로 평점 average 생성
                point.append(score['score'])
                intPoint = list(map(int, point))
                sumPoint = sum(intPoint)
            result = sumPoint / len(point)
            average = f'{result: .1f}'
        db.restaurant.update_one({'name': sh['name']}, {'$set': {'like': average}})     # 해당 식당 db에 average 업데이트

    return render_template('line_base.html', shop=shop, title=title, stations=stations)


# 리뷰 페이지
@app.route('/review/<keyword>', methods=['GET'])
def review(keyword):
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})

    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))

    array = []
    stations = []
    station = list(db.restaurant.find({}, {'_id': False}))
    title = list(db.restaurant_review.find({}, {"_id": False}))
    current_station = 0
    for re in station:
        array.append(re['place'])
        if keyword == re['name']:
            current_station = re['place']

    for re in array:
        if re not in stations:
            stations.append(re)
    # 리뷰 점수 업데이트
    shop = list(db.restaurant.find({'place': current_station}).sort('like', -1))
    for sh in shop:
        allScore = list(db.restaurant_review.find({'shop': sh['name']}))  # 해당 식당에 해당하는 리뷰 정보 allScore[] 생성
        point = []
        if not allScore:
            average = 0  # 해당 식당에 리뷰가 없으면 평점 0으로 초기화
        else:
            for score in allScore:  # 해당 식당에 리뷰가 있으면 (총 별점의 합/ 리뷰의 개수)으로 평점 average 생성
                point.append(score['score'])
                intPoint = list(map(int, point))
                sumPoint = sum(intPoint)
            result = sumPoint / len(point)
            average = f'{result: .1f}'
        db.restaurant.update_one({'name': sh['name']}, {'$set': {'like': average}})  # 해당 식당 db에 average 업데이트

    return render_template('review.html', shop=station, stations=stations, review=title, word=keyword,
                           user_info=user_info)


# 리뷰작성
@app.route('/api/review_create', methods=['POST'])
def review_create():
    # 리뷰 저장
    shop_receive = request.form["shop_give"]
    score_receive = request.form["score_give"]
    reviews_receive = request.form["reviews_give"]
    date_receive = request.form["date_give"]
    img_receive = request.form["img_give"]
    user_name = request.form["user_give"]

    doc ={
        "reviews": reviews_receive,
        "score": score_receive,
        "shop": shop_receive,
        "date": date_receive,
        "img" : img_receive,
        "user" : user_name
    }
    db.restaurant_review.insert_one(doc)
    station = list(db.restaurant.find({}, {'_id': False}))
    for re in station:
        if shop_receive == re['name']:
            current_station = re['place']
    shop = list(db.restaurant.find({'place': current_station}).sort('like', -1))
    # 리뷰 점수 업데이트
    for sh in shop:
        allScore = list(db.restaurant_review.find({'shop': sh['name']}))  # 해당 식당에 해당하는 리뷰 정보 allScore[] 생성
        point = []
        if not allScore:
            average = score_receive  # 해당 식당에 리뷰가 없으면 평점 0으로 초기화
        else:
            for score in allScore:  # 해당 식당에 리뷰가 있으면 (총 별점의 합/ 리뷰의 개수)으로 평점 average 생성
                point.append(score['score'])
                intPoint = list(map(int, point))
                sumPoint = sum(intPoint)
            result = sumPoint / len(point)
            average = f'{result: .1f}'

        db.restaurant.update_one({'name': sh['name']}, {'$set': {'like': average}})  # 해당 식당 db에 average 업데이트

    return jsonify({'msg': '리뷰가 저장 되었습니다!!'})


# 리뷰 보기
@app.route('/my/reviews', methods=['GET'])
def review_show():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        aa = [user_info]
        my_reviews = list(db.restaurant_review.find({}, {"_id": False}))
        return render_template('myReview.html', review=my_reviews, user=aa)

    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))




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
    review_Length = list(db.restaurant_review.find({"shop": review_name}))

    if len(review_Length) == 1:  ## 마지막 리뷰를 지우면 평점 0으로 초기화
        db.restaurant.update_one({"name": review_name}, {'$set': {'like': 0}})
    review_desc = request.form["review_desc"]
    db.restaurant_review.delete_one({'shop': review_name, 'reviews': review_desc})

    shop = list(db.restaurant.find({'name': review_name}).sort('like', -1))
    # 리뷰 점수 업데이트
    for sh in shop:
        allScore = list(db.restaurant_review.find({'shop': sh['name']}))  # 해당 식당에 해당하는 리뷰 정보 allScore[] 생성
        point = []
        if not allScore:
            average = 0  # 해당 식당에 리뷰가 없으면 평점 0으로 초기화
        else:
            for score in allScore:  # 해당 식당에 리뷰가 있으면 (총 별점의 합/ 리뷰의 개수)으로 평점 average 생성
                point.append(score['score'])
                intPoint = list(map(int, point))
                sumPoint = sum(intPoint)
            result = sumPoint / len(point)
            average = f'{result: .1f}'
        db.restaurant.update_one({'name': sh['name']}, {'$set': {'like': average}})  # 해당 식당 db에 average 업데이트


    return jsonify({'msg': '삭제가 완료되었습니다!'})


## 메인
if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
