use inventoryman;
CREATE TABLE Product (
    product_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    quantity INT NOT NULL
);

CREATE TABLE Location (
    location_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE ProductMovement (
    movement_id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    from_location VARCHAR(50),
    to_location VARCHAR(50),
    product_id VARCHAR(50) NOT NULL,
    qty INT NOT NULL,
    FOREIGN KEY (from_location) REFERENCES Location(location_id),
    FOREIGN KEY (to_location) REFERENCES Location(location_id),
    FOREIGN KEY (product_id) REFERENCES Product(product_id)
);

CREATE TABLE LocationProduct (
    product_id VARCHAR(50),
    location_id VARCHAR(50),
    qty INT NOT NULL DEFAULT 0,
    PRIMARY KEY (product_id, location_id),
    FOREIGN KEY (product_id) REFERENCES Product(product_id),
    FOREIGN KEY (location_id) REFERENCES Location(location_id)
);

INSERT INTO Product (product_id, name, quantity) VALUES
('P001', 'Apple iPhone', 100),
('P002', 'Samsung TV', 50);

INSERT INTO Location (location_id, name) VALUES
('L001', 'Warehouse A'),
('L002', 'Warehouse B');









