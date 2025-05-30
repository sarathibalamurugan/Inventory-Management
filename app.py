from flask import Flask, render_template, request, redirect, flash
from flask_mysqldb import MySQL
from MySQLdb.cursors import DictCursor
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'secret_key'

# MySQL Config
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Sarathi@1234'  
app.config['MYSQL_DB'] = 'inventoryman'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/products')
def products():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM Product")
    products = cur.fetchall()
    return render_template('products.html', products=products)

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        pid = request.form['product_id']
        name = request.form['name']
        qty = int(request.form['quantity'])
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO Product (product_id, name, quantity) VALUES (%s, %s, %s)", (pid, name, qty))
        mysql.connection.commit()
        flash('Product added successfully.')
        return redirect('/products')
    return render_template('add_product.html')

@app.route('/update_product/<product_id>', methods=['GET', 'POST'])
def update_product(product_id):
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        name = request.form['name']
        quantity = int(request.form['quantity'])

        cur.execute("""
            UPDATE Product SET name = %s, quantity = %s
            WHERE product_id = %s
        """, (name, quantity, product_id))
        mysql.connection.commit()
        flash("Product updated successfully.")
        return redirect('/products')

    # GET: show existing product
    cur.execute("SELECT * FROM Product WHERE product_id = %s", (product_id,))
    product = cur.fetchone()
    return render_template('update_product.html', product=product)


@app.route('/locations')
def locations():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM Location")
    locations = cur.fetchall()
    return render_template('locations.html', locations=locations)

@app.route('/add_location', methods=['GET', 'POST'])
def add_location():
    if request.method == 'POST':
        lid = request.form['location_id']
        name = request.form['name']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO Location (location_id, name) VALUES (%s, %s)", (lid, name))
        mysql.connection.commit()
        flash('Location added successfully.')
        return redirect('/locations')
    return render_template('add_location.html')

@app.route('/edit_location/<location_id>', methods=['GET', 'POST'])
def edit_location(location_id):
    cur = mysql.connection.cursor()
    
    if request.method == 'POST':
        name = request.form['name']
        cur.execute("UPDATE Location SET name = %s WHERE location_id = %s", (name, location_id))
        mysql.connection.commit()
        flash('Location updated successfully.')
        return redirect('/locations')
    
    cur.execute("SELECT * FROM Location WHERE location_id = %s", (location_id,))
    location = cur.fetchone()
    return render_template('edit_location.html', location=location)


@app.route('/movements', methods=['GET', 'POST'])
def movements():
    cur = mysql.connection.cursor()  
    cur.execute("SELECT product_id, name FROM Product")
    products = cur.fetchall()
    cur.execute("SELECT location_id, name FROM Location")
    locations = cur.fetchall()

    if request.method == 'POST':
        product_id = request.form['product_id']
        from_location = request.form['from_location']
        to_location = request.form['to_location']
        qty = int(request.form['quantity'])
        timestamp = datetime.now()

        if from_location:
            # Check available quantity in from_location
            cur.execute("""
                SELECT qty FROM LocationProduct 
                WHERE product_id = %s AND location_id = %s
            """, (product_id, from_location))
            row = cur.fetchone()
            available_qty = row['qty'] if row else 0

            if qty > available_qty:
                flash(f'Insufficient quantity at source. Only {available_qty} units available.')
                return redirect('/movements')

            # Deduct from source location
            cur.execute("""
                UPDATE LocationProduct SET qty = qty - %s
                WHERE product_id = %s AND location_id = %s
            """, (qty, product_id, from_location))
        else:
            # Movement from outside, check Product table
            cur.execute("SELECT quantity FROM Product WHERE product_id = %s", (product_id,))
            product = cur.fetchone()
            if not product:
                flash("Product not found.")
                return redirect('/movements')

            available_qty = product['quantity']
            if qty > available_qty:
                flash(f'Insufficient product quantity. Only {available_qty} units available in Product.')
                return redirect('/movements')

            # Deduct from Product master quantity
            cur.execute("UPDATE Product SET quantity = quantity - %s WHERE product_id = %s", (qty, product_id))

        # Add to target location
        cur.execute("""
            INSERT INTO LocationProduct (product_id, location_id, qty)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE qty = qty + VALUES(qty)
        """, (product_id, to_location, qty))

        # Record the movement
        cur.execute("""
            INSERT INTO ProductMovement (timestamp, from_location, to_location, product_id, qty)
            VALUES (%s, %s, %s, %s, %s)
        """, (timestamp, from_location or None, to_location, product_id, qty))

        mysql.connection.commit()
        flash('Product movement recorded.')
        return redirect('/movements')

    return render_template('movements.html', products=products, locations=locations)


@app.route('/report')
def report():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT 
            l.name AS location_name,
            p.name AS product_name,
            lp.qty
        FROM LocationProduct lp
        JOIN Location l ON lp.location_id = l.location_id
        JOIN Product p ON lp.product_id = p.product_id
        WHERE lp.qty > 0
        ORDER BY l.name, p.name
    """)
    movements = cur.fetchall()
    return render_template('report.html', movements=movements)


@app.route('/sell', methods=['GET', 'POST'])
def sell_product():
    cur = mysql.connection.cursor()

    # Get products and locations for the dropdown
    cur.execute("SELECT product_id, name FROM Product")
    products = cur.fetchall()
    cur.execute("SELECT location_id, name FROM Location")
    locations = cur.fetchall()

    if request.method == 'POST':
        product_id = request.form['product_id']
        location_id = request.form['location_id']
        qty = int(request.form['quantity'])

        # Check available quantity at the location
        cur.execute("""
            SELECT qty FROM LocationProduct 
            WHERE product_id = %s AND location_id = %s
        """, (product_id, location_id))
        row = cur.fetchone()
        available_qty = row['qty'] if row else 0

        if qty > available_qty:
            flash(f'Not enough stock. Only {available_qty} units available at {location_id}.')
            return redirect('/sell')

        # Deduct from location
        cur.execute("""
            UPDATE LocationProduct 
            SET qty = qty - %s 
            WHERE product_id = %s AND location_id = %s
        """, (qty, product_id, location_id))

        # Optional: Record sale in a Sale table (not implemented here)
        mysql.connection.commit()
        flash(f'Successfully sold {qty} units of {product_id} from {location_id}.')
        return redirect('/sell')

    return render_template('sell_product.html', products=products, locations=locations)


if __name__ == '__main__':
    app.run(debug=True)
