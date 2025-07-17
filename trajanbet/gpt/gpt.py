from trajanbet import app
from trajanbet.models import get_db
import datetime
import flask
from datetime import datetime
from math import gcd
from flask import Flask, render_template, request, redirect, url_for
from config import GPT_API_KEY
import openai

client = openai.OpenAI(api_key=GPT_API_KEY)

@app.route("/askhadrian", methods=["GET"])
def askhadrian():
    return flask.render_template("askhadrian.html")

@app.route("/gptasker", methods=["POST"])
def gptasker():
    user_input = flask.request.json['message']

    with open("system_prompt.txt", "r") as file:
        system_prompt = file.read()
    
    with open("broker_gpt.txt", "r") as file:
        broker_prompt = file.read()

    with open("calc_prompt.txt", "r") as file:
        calc_prompt = file.read()
     
    response1 = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ],
        max_tokens=500,
        temperature=0.6
    )

    gpt_reply = response1.choices[0].message.content.strip()

    # Check for our special flag
    if gpt_reply.endswith("39jko"):
        db = get_db()

        res = db.execute("""
            SELECT hedge_val, udogs, favs, sport, bettype, udogs_odds, favs_odds,
                   udogs_book, favs_book, commence_time
            FROM all_lines
            ORDER BY hedge_val DESC
            LIMIT 250;
        """)
        raw_lines = res.fetchall()

        current_time = datetime.now()
        top_lines = []
        counter = 0
        for line in raw_lines:
            game_time = datetime.strptime(line["commence_time"], "%Y-%m-%d %H:%M:%S")
            if game_time <= current_time:
                line["live"] = "Live"
            else:
                line["live"] = "Upcoming"
            
            if line["live"] == "Live":
                continue
            
            top_lines.append(line)
            counter += 1
            if counter >= 40:
                break

        line_info = "\n".join([
            f"{i+1}) Sport: {row['sport']}, Type: {row['bettype']}, HV: {row['hedge_val']:.2f}, "
            f"Underdog: {row['udogs']} ({row['udogs_odds']}) via {row['udogs_book']}, "
            f"Favorite: {row['favs']} ({row['favs_odds']}) via {row['favs_book']}, Time: {row['commence_time']}, "
            f"The bonus sports book for this bet is {row['udogs_book']}"
            for i, row in enumerate(top_lines)
        ])

        response2 = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": broker_prompt},
                {"role": "user", "content": f"The user asked: '{user_input}'. Here are the best 3 matched betting lines:\n{line_info}\nRespond using this data in a natural helpful tone. DO NOT END MESSAGE WITH 39jko FLAG!!"}
            ],
            max_tokens=600,
            temperature=0.6
        )

        final_reply = response2.choices[0].message.content.strip()


        if final_reply.endswith("39jko"):
            final_reply = final_reply[:-5].rstrip(". ").strip()
        elif final_reply.endswith("39jko."):
            final_reply = final_reply[:-6].rstrip(". ").strip()

        return flask.jsonify({"reply": final_reply})

    elif gpt_reply.endswith("45n91") or gpt_reply.endswith("45n91."):
        print("entered here successfully!!!")
        db = get_db()

        res = db.execute("""
            SELECT arb_margin, udogs, favs, sport, bettype, udogs_odds, favs_odds,
                   udogs_book, favs_book, commence_time
            FROM arb_lines
            ORDER BY arb_margin DESC;
        """)
        raw_lines = res.fetchall()

        current_time = datetime.now()
        top_lines = []
        for line in raw_lines:
            game_time = datetime.strptime(line["commence_time"], "%Y-%m-%d %H:%M:%S")
            if game_time <= current_time:
                line["live"] = "Live"
            else:
                line["live"] = "Upcoming"
            
            if line["live"] == "Live":
                continue
            
            top_lines.append(line)

        line_info = "\n".join([
            f"{i+1}) Sport: {row['sport']}, Type: {row['bettype']}, Arb_Margin: {row['arb_margin']:.2f}, "
            f"Underdog: {row['udogs']} ({row['udogs_odds']}) via {row['udogs_book']}, "
            f"Favorite: {row['favs']} ({row['favs_odds']}) via {row['favs_book']}, Time: {row['commence_time']}"
            for i, row in enumerate(top_lines)
        ])

        print(line_info)

        response2 = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": broker_prompt},
                {"role": "user", "content": f"The user asked: '{user_input}'. Here are the best 3 arbitrage lines:\n{line_info}\nRespond using this data in a natural helpful tone. Make sentences with those numbers naturally. DO NOT END MESSAGE WITH 45n91 FLAG!!"}
            ],
            max_tokens=600,
            temperature=0.6
        )

        final_reply = response2.choices[0].message.content.strip()
        if final_reply.endswith("45n91"):
            final_reply = final_reply[:-5].rstrip(". ").strip()
        elif final_reply.endswith("45n91."):
            final_reply = final_reply[:-6].rstrip(". ").strip()

        return flask.jsonify({"reply": final_reply})

    elif gpt_reply.endswith("vo9bv") or gpt_reply.endswith("vo9bv."):
        response2 = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": calc_prompt},
                {"role": "user", "content": f"The user asked: '{user_input}'. Solve and give answer, accordingly, Hadrian"}
            ],
            max_tokens=600,
            temperature=0.6
        )

        final_reply = response2.choices[0].message.content.strip()
        if final_reply.endswith("vo9bv"):
            final_reply = final_reply[:-5].rstrip(". ").strip()
        elif final_reply.endswith("vo9bv."):
            final_reply = final_reply[:-6].rstrip(". ").strip()

        return flask.jsonify({"reply": final_reply})
    
    else:
        return flask.jsonify({"reply": gpt_reply})
    
    
