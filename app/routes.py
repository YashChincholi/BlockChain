from flask import Blueprint, render_template, request, redirect, url_for
from blockchain.blockchain import Blockchain

# Initialize the blockchain
blockchain = Blockchain()

main = Blueprint("main", __name__)

@main.route("/")
def index():
    return render_template("index.html", blockchain=blockchain.chain)

@main.route("/add", methods=["GET", "POST"])
def add_block():
    if request.method == "POST":
        data = request.form.get("data")
        if data:
            blockchain.add_block(data)
            return redirect(url_for("main.index"))
    return render_template("add_block.html")
