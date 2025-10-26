import logging
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash
from blockchain.blockchain import Blockchain

logger = logging.getLogger(__name__)

blockchain = Blockchain()

main = Blueprint("main", __name__)

@main.route("/")
def index():
    try:
        stats = blockchain.get_stats()
        return render_template("index.html", blockchain=blockchain.chain, stats=stats)
    except Exception as e:
        logger.error(f"Error rendering index: {e}")
        return render_template("error.html", error=str(e)), 500

@main.route("/add", methods=["GET", "POST"])
def add_block():
    if request.method == "POST":
        data = request.form.get("data", "").strip()

        if not data:
            flash("Block data cannot be empty", "error")
            return render_template("add_block.html")

        try:
            blockchain.add_block(data)
            flash(f"Block added successfully!", "success")
            return redirect(url_for("main.index"))
        except Exception as e:
            logger.error(f"Error adding block: {e}")
            flash(f"Error adding block: {str(e)}", "error")
            return render_template("add_block.html")

    return render_template("add_block.html")

@main.route("/validate")
def validate():
    try:
        is_valid, invalid_blocks = blockchain.is_chain_valid()
        if is_valid:
            flash("Blockchain is valid!", "success")
        else:
            flash(f"Blockchain is invalid! Invalid blocks: {invalid_blocks}", "error")
        return redirect(url_for("main.index"))
    except Exception as e:
        logger.error(f"Error validating blockchain: {e}")
        flash(f"Error validating blockchain: {str(e)}", "error")
        return redirect(url_for("main.index"))

@main.route("/api/blockchain")
def api_blockchain():
    try:
        return jsonify({
            'success': True,
            'blockchain': blockchain.get_chain_as_dict(),
            'stats': blockchain.get_stats()
        })
    except Exception as e:
        logger.error(f"API error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@main.route("/api/add", methods=["POST"])
def api_add_block():
    try:
        data = request.json.get("data", "").strip()

        if not data:
            return jsonify({'success': False, 'error': 'Block data cannot be empty'}), 400

        new_block = blockchain.add_block(data)
        return jsonify({
            'success': True,
            'message': 'Block added successfully',
            'block': new_block.to_dict(),
            'stats': blockchain.get_stats()
        })
    except Exception as e:
        logger.error(f"API error adding block: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@main.route("/api/validate")
def api_validate():
    try:
        is_valid, invalid_blocks = blockchain.is_chain_valid()
        return jsonify({
            'success': True,
            'is_valid': is_valid,
            'invalid_blocks': invalid_blocks
        })
    except Exception as e:
        logger.error(f"API error validating: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
