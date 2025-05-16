from flask import Flask, render_template, request, redirect, url_for, session, send_file
import pandas as pd
import io

app = Flask(__name__)
app.secret_key = "secure_key"  # 세션 저장을 위한 비밀키

# 등급 계산 함수
def calculate_grade(score):
    if score >= 90: return 1
    elif score >= 80: return 2
    elif score >= 70: return 3
    elif score >= 60: return 4
    elif score >= 50: return 5
    elif score >= 40: return 6
    elif score >= 30: return 7
    elif score >= 20: return 8
    else: return 9

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        session["exam_name"] = request.form.get("exam_name")
        session["correct_answers"] = request.form.getlist("correct_answers")
        session["three_points"] = request.form.get("three_points")

        students = []
        names = request.form.getlist("name")
        answers = request.form.getlist("answers")

        for i in range(len(names)):
            student_answers = answers[i * 45 : (i + 1) * 45]  
            students.append({"name": names[i], "answers": student_answers})

        session["students"] = students
        return redirect(url_for("grade"))

    return render_template(
        "index.html",
        exam_name=session.get("exam_name", ""),
        correct_answers=session.get("correct_answers", [""] * 45),
        three_points=session.get("three_points", ""),
        students=session.get("students", [{"name": "", "answers": [""] * 45}]),
    )

@app.route("/grade")
def grade():
    if "correct_answers" not in session or "students" not in session:
        return redirect(url_for("index"))

    correct_answers = session["correct_answers"]
    three_points = list(map(int, session["three_points"].split(","))) if session["three_points"] else []
    students = session["students"]

    results = []
    for student in students:
        name = student["name"]
        answers = student["answers"]

        listening_score = 0
        reading_score = 0
        wrong_answers = []

        for i in range(45):
            if answers[i] == correct_answers[i]:  
                score = 3 if (i + 1) in three_points else 2
                if i < 17:
                    listening_score += score
                else:
                    reading_score += score
            else:
                 wrong_answers.append(f"{i+1}번")   # 틀린 문항 기록

        total_score = listening_score + reading_score
        grade = calculate_grade(total_score)

        results.append({
            "이름": name,
            "총점": total_score,
            "등급": grade,
            "듣기 점수": listening_score,
            "읽기 점수": reading_score,
            "틀린 문항": ", ".join(wrong_answers) if wrong_answers else "없음"
        })

    session["results"] = results
    return render_template("result.html", results=results, exam_name=session["exam_name"])

@app.route("/export")
def export():
    if "results" not in session or "exam_name" not in session:
        return redirect(url_for("index"))

    exam_name = session["exam_name"].replace(" ", "_")
    column_order = ["이름", "듣기 점수", "읽기 점수", "총점", "등급", "틀린 문항"]
    df = pd.DataFrame(session["results"])[column_order]

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="채점 결과")

    output.seek(0)
    file_name = f"{exam_name}_채점결과.xlsx"
     
    return send_file(output, as_attachment=True, download_name=file_name, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@app.route("/keep-alive")
def keep_alive():
    return "OK"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)


