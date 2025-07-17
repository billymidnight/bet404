from flask import Flask, render_template, request, redirect, url_for
from trajanbet import app
from trajanbet.models import get_db
import datetime
from datetime import datetime
from math import gcd


@app.route("/deleterace/<int:race_id>", methods=["GET"])
def deleterace(race_id):
    """Deletes a race and all related data."""
    db = get_db()

    db.execute(
        "DELETE FROM racebets WHERE horseid IN (SELECT horseid FROM horses WHERE raceid = ?)",
        (race_id,),
    )

    db.execute("DELETE FROM horses WHERE raceid = ?", (race_id,))

    db.execute("DELETE FROM races WHERE raceid = ?", (race_id,))

    db.commit()

    return redirect(url_for("raceviewer"))
