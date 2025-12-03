import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sari_sari_store.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ----------------------
# MODELS
# ----------------------
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)

    parent = db.relationship('Category', remote_side=[id], backref='subcategories')

    __table_args__ = (db.UniqueConstraint('name', 'parent_id', name='_unique_subcategory_per_parent'),)

    def __repr__(self):
        return f"<Category {self.name}>"


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String, nullable=True)

    category = db.relationship("Category", backref=db.backref("products", lazy=True))

    def __repr__(self):
        return f"<Product {self.name}>"


# ----------------------
# ROUTES
# ----------------------

@app.route('/')
def home():
    # Fetch all products
    products = Product.query.all()

    # Calculate dashboard values
    total_products = len(products)
    total_stock = sum(p.quantity for p in products)
    total_value = sum(p.quantity * p.price for p in products)
    low_stock_items = Product.query.filter(Product.quantity <= 5).count()  # Example threshold

    return render_template(
        "index.html",
        total_products=total_products,
        total_stock=total_stock,
        total_value=total_value,
        low_stock_items=low_stock_items,
        products=products
    )
@app.route('/product_management', methods=['GET', 'POST'])
def product_management():
    categories = Category.query.all()

    if request.method == 'POST':
        name = request.form.get('name')
        category_id = request.form.get('category')  # can be None
        qty = int(request.form.get('qty', 0))
        price = float(request.form.get('price', 0.0))

        # Handle image upload
        image_file = request.files.get('image')
        filename = None
        if image_file and image_file.filename != '':
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(image_path)

        # If no subcategory is selected, use the main category
        if not category_id:
            category_id = request.form.get('main_category')

        # Create new product
        if category_id:
            new_product = Product(
                name=name,
                category_id=int(category_id),
                quantity=qty,
                price=price,
                image=filename
            )
            db.session.add(new_product)
            db.session.commit()

        return redirect(url_for('product_management'))

    # Convert to JSON-safe format for JS
    category_data = [
        {"id": c.id, "name": c.name, "parent_id": c.parent_id}
        for c in categories
    ]

    products = Product.query.all()

    return render_template(
        "product_management.html",
        products=products,
        categories=categories,
        category_data=category_data
    )

# ----------------------
# CATEGORY MANAGEMENT
# ----------------------

@app.route('/add_category', methods=['POST'])
def add_category():
    name = request.form['name'].strip()

    if name:
        existing = Category.query.filter_by(name=name, parent_id=None).first()
        if existing:
            categories = Category.query.all()
            return render_template(
                "categories.html",
                categories=categories,
                error="Category already exists!"
            )
        else:
            new_cat = Category(name=name)
            db.session.add(new_cat)
            db.session.commit()

    return redirect(url_for('manage_categories'))


# ✅ NEW: Add Subcategory
@app.route('/add_subcategory', methods=['POST'])
def add_subcategory():
    name = request.form['name'].strip()
    parent_id = request.form['parent_id']

    if not parent_id:
        categories = Category.query.all()
        return render_template(
            "categories.html",
            categories=categories,
            error="Please select a parent category."
        )

    existing = Category.query.filter_by(name=name, parent_id=parent_id).first()
    if existing:
        categories = Category.query.all()
        return render_template(
            "categories.html",
            categories=categories,
            error="Subcategory already exists under this category!"
        )

    new_sub = Category(name=name, parent_id=parent_id)
    db.session.add(new_sub)
    db.session.commit()

    return redirect(url_for('manage_categories'))


@app.route('/delete_category/<int:id>')
def delete_category(id):
    category = Category.query.get_or_404(id)
    db.session.delete(category)
    db.session.commit()
    return redirect(url_for('product_management'))


@app.route("/edit_category/<int:id>", methods=["GET", "POST"])
def edit_category(id):
    category = Category.query.get_or_404(id)

    if request.method == "POST":
        new_name = request.form["name"].strip()

        existing = Category.query.filter(
            Category.name == new_name,
            Category.id != id,
            Category.parent_id == category.parent_id
        ).first()

        if existing:
            return render_template(
                "edit_category.html",
                category=category,
                error="Category name already exists!"
            )
        else:
            category.name = new_name
            db.session.commit()
            return redirect(url_for("manage_categories"))

    return render_template("edit_category.html", category=category)


@app.route('/categories')
def manage_categories():
    categories = Category.query.all()
    return render_template("categories.html", categories=categories)


# ----------------------
# OTHER ROUTES
# ----------------------

@app.route('/delete/<int:id>')
def delete_product(id):
    product = Product.query.get_or_404(id)
    if product.image:
        img_path = os.path.join(app.config['UPLOAD_FOLDER'], product.image)
        if os.path.exists(img_path):
            os.remove(img_path)
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for('product_management'))


@app.route('/customer_purchase')
def stock_monitoring():
    products = Product.query.all()
    return render_template("customer_purchase.html", products=products)


@app.route("/stock_reports")
def stock_reports():
    products = Product.query.all()
    total_items = sum(p.quantity for p in products)
    total_value = sum(p.quantity * p.price for p in products)

    return render_template(
        "stock_reports.html",
        total_items=total_items,
        total_value=total_value,
        products=products
    )


@app.route('/customer_purchase')
def customer_purchase():
    products = Product.query.all()
    return render_template("customer_purchase.html", products=products)


@app.route('/buy/<int:id>', methods=["POST"])
def buy_product(id):
    product = Product.query.get_or_404(id)
    qty = int(request.form['qty'])

    if qty > 0 and qty <= product.quantity:
        product.quantity -= qty
        db.session.commit()

    return redirect(url_for('customer_purchase'))


@app.route("/edit_product/<int:id>", methods=["GET", "POST"])
def edit_product(id):
    product = Product.query.get_or_404(id)
    categories = Category.query.all()

    if request.method == "POST":
        product.name = request.form["name"]
        product.quantity = request.form["qty"]
        product.price = request.form["price"]
        product.category_id = request.form["category"]

        # Handle new image if uploaded
        image_file = request.files.get('image')
        if image_file and image_file.filename != '':
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(image_path)
            product.image = filename

        db.session.commit()
        return redirect(url_for("product_management"))

    return render_template("edit_product.html", product=product, categories=categories)


# ----------------------
# DB INIT
# ----------------------
with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)
