from flask import Blueprint, render_template, request, abort
from src.models import db
from src.models.research_item import ResearchItem

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    # Fetch latest items (e.g., latest 3) - Placeholder logic
    latest_items = ResearchItem.query.order_by(ResearchItem.upload_date.desc()).limit(3).all()
    return render_template("index.html", latest_items=latest_items)

@main_bp.route("/browse")
def browse():
    # Basic browsing/searching - Placeholder logic
    query = request.args.get("query", "")
    item_type = request.args.get("type", "all")
    
    results_query = ResearchItem.query
    
    if query:
        search_term = f"%{query}%"
        results_query = results_query.filter(
            (ResearchItem.title.like(search_term)) |
            (ResearchItem.author.like(search_term)) |
            (ResearchItem.abstract.like(search_term)) |
            (ResearchItem.keywords.like(search_term))
        )
        
    if item_type != "all":
        results_query = results_query.filter(ResearchItem.item_type == item_type)
        
    # Add pagination later
    results = results_query.order_by(ResearchItem.upload_date.desc()).all()
    
    return render_template("browse.html", results=results, query=query, item_type=item_type)

@main_bp.route("/item/<int:item_id>")
def view_item(item_id):
    item = ResearchItem.query.get_or_404(item_id)
    # Convert keywords string to list for template
    if item.keywords:
        item.keywords_list = [k.strip() for k in item.keywords.split(",")]
    else:
        item.keywords_list = []
    return render_template("view_item.html", item=item)

@main_bp.route("/donate")
def donate():
    return render_template("donate.html")

# Add routes for about, privacy policy, contact later

