from flask import Flask
from flask import render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)  #アプリケーションのインスタンス化
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///quiz.db"  #データベース作成のパス
db = SQLAlchemy(app) #データベース生成


class Quizset(db.Model):
    quizsetname = db.Column(db.String)
    id = db.Column(db.Integer, primary_key=True)  
    quiz_sentence = db.Column(db.String(100),nullable=False) 
    answer = db.Column(db.String(20), nullable=False) 
    reading = db.Column(db.String(20), nullable=False)

class Quizsettype(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)  


#トップ画面
@app.route("/", methods=["GET","POST"])
def top():
        return render_template("html/top.html") 


#クイスセット管理画面。クイスセット一覧の表示
@app.route("/managetop", methods=["GET","POST"]) 
def managetop():
    if request.method == "GET":
        quiz_tuple = Quizset.query.with_entities(Quizsettype.name).all()  
        quiz_list = [n[0] for n in quiz_tuple]  
        quizsetname = sorted(set(quiz_list)) 
        return render_template("html/managetop.html", quizsetname=quizsetname)


#指定したクイズセットのクイスの管理画面。クイズ一覧を表示。
@app.route("/<string:quizsetname>/manage_quizset", methods=["GET","POST"])
def manage_quizset(quizsetname):
    if request.method == "GET":
        quizes = Quizset.query.filter_by(quizsetname = quizsetname)
        return render_template("html/manage_quizset.html",quizes=quizes,quizsetname=quizsetname)


#クイズの編集。
@app.route("/<int:id>/manage_quiz", methods=["GET","POST"])  
def manage_quiz(id):
    if request.method == "GET":
        quizes = Quizset.query.filter_by(id=id)
        return render_template("html/manage_quiz.html",quizes=quizes)
    else:
        quiz = Quizset.query.filter_by(id=id)
        post = Quizset.query.get(id) 
        post.quiz_sentence = request.form.get("quiz_sentence") 
        post.answer = request.form.get("answer")
        post.reading = request.form.get("reading")
        quizsetname = post.quizsetname 
        quizes = Quizset.query.filter_by(quizsetname = quizsetname)
        if post.quiz_sentence != "" and post.answer != "" and post.reading != "":
            db.session.commit() 
            return render_template("html/manage_quizset.html",quizes=quizes,quizsetname=quizsetname)
        else:
            error = "入力していない項目があります"
            return render_template("html/manage_quiz.html",quizes=quiz,error=error) 
    

#クイズの削除。
@app.route("/<int:id>/quiz_delete", methods=["GET"])  
def quiz_delete(id):
    if request.method == "GET":
        post = Quizset.query.get(id)
        quizsetname = post.quizsetname
        quizes =  Quizset.query.filter_by(quizsetname = quizsetname)
        db.session.delete(post)
        db.session.commit()
        return render_template("html/manage_quizset.html",quizes=quizes,quizsetname=quizsetname)
    

#クイズセットの削除。
@app.route("/<string:quizsetname>/quizset_delete", methods=["GET"])  
def quizset_delete(quizsetname):
    quizes =  Quizsettype.query.filter_by(name = quizsetname).delete()
    quizes2 =  Quizset.query.filter_by(quizsetname = quizsetname).delete()
    db.session.commit()

    quiz_tuple = Quizset.query.with_entities(Quizsettype.name).all()
    quiz_list = [n[0] for n in quiz_tuple]
    quizsetname = sorted(set(quiz_list))
    return render_template("html/managetop.html", quizsetname=quizsetname)


#新規クイズセットの作成。
@app.route("/quizsetcreate", methods=["GET","POST"]) 
def quizsetcreate():
    if request.method == "POST":
        name = request.form.get("name")
        if name != "":
            post = Quizsettype(name=name) 
            db.session.add(post)  
            db.session.commit()  

            quiz_tuple = Quizset.query.with_entities(Quizsettype.name).all()
            quiz_list = [n[0] for n in quiz_tuple]
            quizsetname = sorted(set(quiz_list))
            return render_template("html/managetop.html",quizsetname=quizsetname)
        else:
            error = "クイズセット名を入力してください"
            return render_template("html/quizsetcreate.html",error=error)
    else:
        return render_template("html/quizsetcreate.html")
     

#新規クイズの作成。
@app.route("/<string:quizsetname>/quizcreate", methods=["GET","POST"])  
def quizcreate(quizsetname):
    if request.method == "POST": 
        quiz_sentence = request.form.get("quiz_sentence") 
        answer = request.form.get("answer")
        reading = request.form.get("reading")

        if quiz_sentence != "" and answer != "" and reading != "":
            quizsetname = quizsetname
            post = Quizset(quiz_sentence=quiz_sentence, answer=answer, reading=reading, quizsetname=quizsetname)

            db.session.add(post) 
            db.session.commit()  

            quizes = Quizset.query.filter_by(quizsetname = quizsetname)
            return render_template("html/manage_quizset.html",quizes=quizes,quizsetname=quizsetname) 
        else:
            error = "入力していない項目があります"
            return render_template("html/quizcreate.html",error=error,quizsetname=quizsetname) 
    else:
        return render_template("html/quizcreate.html",quizsetname=quizsetname)
    

#挑戦する問題を選択する画面。
@app.route("/solvetop", methods=["GET","POST"])
def solvetop():
        global correct,order
        correct,order = 0,-1
        quiz_tuple = Quizset.query.with_entities(Quizset.quizsetname).all()
        quiz_list = [n[0] for n in quiz_tuple]
        quizsetname = sorted(set(quiz_list))
        return render_template("html/solvetop.html", quizsetname=quizsetname)


#クイズを解いている時の画面。問題の表示と正解数の記録、正誤の判定等を行う
order,correct,end = -1,0,False   #何問目か,正解数,全問題を解いたか否か
@app.route("/<string:quizsetname>/solving", methods=["GET","POST"])  
def solving(quizsetname):
    global order,correct,end
    if request.method == "GET":
        ans = None
        quizes = Quizset.query.filter_by(quizsetname = quizsetname)
        order += 1
        print(quizes)
        return render_template("html/solving.html",quiz=quizes[order])
    else:
        ans = request.form.get('reading')
        quizes = Quizset.query.filter_by(quizsetname = quizsetname)
        answer_list = []
        for i in quizes:   
            answer_list.append(i.reading)   

        if order == len(answer_list) - 1:
            end = True
            
        if ans == answer_list[order]:
            correct += 1
            return render_template("html/solving.html",quiz=quizes[order],rw = "正解",end=end,ans=ans)
        else:
            return render_template("html/solving.html",quiz=quizes[order],rw = "不正解",end=end,ans=ans)
        

#クイズの結果の表示
@app.route("/result", methods=["GET","POST"]) 
def result():
    global correct
    global order
    global end
    if request.method == "GET":
        quiz_tuple = Quizset.query.with_entities(Quizset.quizsetname).all()
        quiz_list = [n[0] for n in quiz_tuple]
        quizsetname = sorted(set(quiz_list))
        correct,order,end = 0,-1,False
        return render_template("html/solvetop.html", quizsetname=quizsetname)
    else:
        quiz_tuple = Quizset.query.with_entities(Quizset.quizsetname).all()
        quiz_list = [n[0] for n in quiz_tuple]
        quizsetname = sorted(set(quiz_list))

        quizsetname = request.form.get("quizsetname")

        quizes = Quizset.query.filter_by(quizsetname = quizsetname) #クエリが表示
        quiz_sum = []
        for i in quizes:   
            quiz_sum.append(i.answer)
        return render_template("html/result.html",correct=correct,quiz_sum=len(quiz_sum))