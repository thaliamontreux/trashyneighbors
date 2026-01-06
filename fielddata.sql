SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS=0;
START TRANSACTION;

DROP TABLE IF EXISTS ref_import_manifest;
DROP TABLE IF EXISTS ref_email_template;
DROP TABLE IF EXISTS ref_user_submitted_vehicle_model_status;
DROP TABLE IF EXISTS ref_nuisance_item;
DROP TABLE IF EXISTS ref_nuisance_category;
DROP TABLE IF EXISTS ref_vehicle_make;
DROP TABLE IF EXISTS ref_vehicle_condition;
DROP TABLE IF EXISTS ref_vehicle_type;
DROP TABLE IF EXISTS ref_vehicle_color;
DROP TABLE IF EXISTS ref_zip_city;
DROP TABLE IF EXISTS ref_reference_table;

CREATE TABLE IF NOT EXISTS ref_reference_table (
  ref_table_id INT NOT NULL AUTO_INCREMENT,
  table_name VARCHAR(128) NOT NULL,
  key_fields_json JSON NOT NULL,
  upsert_mode VARCHAR(32) NOT NULL,
  PRIMARY KEY (ref_table_id),
  UNIQUE KEY uk_ref_reference_table_name (table_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ref_vehicle_color (
  color_id INT NOT NULL AUTO_INCREMENT,
  color_name VARCHAR(128) NOT NULL,
  PRIMARY KEY (color_id),
  UNIQUE KEY uk_ref_vehicle_color_name (color_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ref_vehicle_type (
  type_id INT NOT NULL AUTO_INCREMENT,
  type_name VARCHAR(128) NOT NULL,
  PRIMARY KEY (type_id),
  UNIQUE KEY uk_ref_vehicle_type_name (type_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ref_vehicle_condition (
  condition_id INT NOT NULL AUTO_INCREMENT,
  condition_name VARCHAR(255) NOT NULL,
  PRIMARY KEY (condition_id),
  UNIQUE KEY uk_ref_vehicle_condition_name (condition_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ref_vehicle_make (
  make_id INT NOT NULL AUTO_INCREMENT,
  make_name VARCHAR(128) NOT NULL,
  PRIMARY KEY (make_id),
  UNIQUE KEY uk_ref_vehicle_make_name (make_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ref_nuisance_category (
  category_id INT NOT NULL AUTO_INCREMENT,
  category_name VARCHAR(255) NOT NULL,
  PRIMARY KEY (category_id),
  UNIQUE KEY uk_ref_nuisance_category_name (category_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ref_nuisance_item (
  item_id INT NOT NULL AUTO_INCREMENT,
  category_id INT NOT NULL,
  item_name VARCHAR(255) NOT NULL,
  PRIMARY KEY (item_id),
  UNIQUE KEY uk_ref_nuisance_item (category_id, item_name),
  KEY idx_ref_nuisance_item_name (item_name),
  CONSTRAINT fk_ref_nuisance_item_category FOREIGN KEY (category_id)
    REFERENCES ref_nuisance_category(category_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ref_zip_city (
  zip5 CHAR(5) NOT NULL,
  city VARCHAR(128) NOT NULL,
  state CHAR(2) NOT NULL,
  PRIMARY KEY (zip5, city, state),
  KEY idx_ref_zip_city_zip5 (zip5),
  KEY idx_ref_zip_city_state_city (state, city)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ref_email_template (
  template_id INT NOT NULL AUTO_INCREMENT,
  template_key VARCHAR(128) NOT NULL,
  subject VARCHAR(255) NOT NULL,
  body_text TEXT NOT NULL,
  PRIMARY KEY (template_id),
  UNIQUE KEY uk_ref_email_template_key (template_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ref_user_submitted_vehicle_model_status (
  status_id INT NOT NULL AUTO_INCREMENT,
  status_key VARCHAR(64) NOT NULL,
  status_label VARCHAR(255) NOT NULL,
  PRIMARY KEY (status_id),
  UNIQUE KEY uk_ref_user_vehicle_model_status_key (status_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ref_import_manifest (
  import_manifest_id INT NOT NULL AUTO_INCREMENT,
  import_key VARCHAR(128) NOT NULL,
  priority INT NULL,
  source_name VARCHAR(255) NULL,
  source_url VARCHAR(2048) NULL,
  licensing_note TEXT NULL,
  installer_behavior TEXT NULL,
  tables_target_json JSON NOT NULL,
  references_json JSON NOT NULL,
  PRIMARY KEY (import_manifest_id),
  UNIQUE KEY uk_ref_import_manifest_key (import_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO ref_reference_table (table_name, key_fields_json, upsert_mode) VALUES
('ref_vehicle_color', '["color_name"]', 'upsert'),
('ref_vehicle_type', '["type_name"]', 'upsert'),
('ref_vehicle_condition', '["condition_name"]', 'upsert'),
('ref_vehicle_make', '["make_name"]', 'upsert'),
('ref_nuisance_category', '["category_name"]', 'upsert'),
('ref_nuisance_item', '["category_name","item_name"]', 'upsert'),
('ref_zip_city', '["zip5","city","state"]', 'upsert'),
('ref_email_template', '["template_key"]', 'upsert'),
('ref_user_submitted_vehicle_model_status', '["status_key"]', 'upsert')
ON DUPLICATE KEY UPDATE key_fields_json=VALUES(key_fields_json), upsert_mode=VALUES(upsert_mode);

INSERT INTO ref_vehicle_color (color_name) VALUES
('Black'),
('White'),
('Gray'),
('Silver'),
('Red'),
('Blue'),
('Green'),
('Yellow'),
('Orange'),
('Brown'),
('Purple'),
('Pink'),
('Matte (Modifier)'),
('Metallic (Modifier)'),
('Two-tone (Modifier)'),
('Faded (Modifier)'),
('Rusted (Modifier)'),
('Primer (Modifier)'),
('Peeling Paint (Modifier)')
ON DUPLICATE KEY UPDATE color_name=VALUES(color_name);

INSERT INTO ref_vehicle_type (type_name) VALUES
('Sedan'),
('Coupe'),
('Hatchback'),
('Wagon'),
('SUV'),
('Crossover'),
('Pickup Truck'),
('Van (Cargo)'),
('Van (Passenger)'),
('Minivan'),
('Box Truck'),
('Semi-Truck'),
('Motorcycle'),
('Scooter'),
('RV (Class A)'),
('RV (Class B)'),
('RV (Class C)'),
('Camper Trailer'),
('Fifth Wheel'),
('Boat'),
('ATV'),
('UTV')
ON DUPLICATE KEY UPDATE type_name=VALUES(type_name);

INSERT INTO ref_vehicle_condition (condition_name) VALUES
('Operational'),
('Non-Operational'),
('Abandoned'),
('Wrecked'),
('Burned'),
('Stripped'),
('Missing Parts'),
('On Blocks'),
('Flat Tires'),
('Overgrown Around Vehicle'),
('Filled With Trash'),
('Rodent Infested')
ON DUPLICATE KEY UPDATE condition_name=VALUES(condition_name);

INSERT INTO ref_vehicle_make (make_name) VALUES
('Ford'),
('Chevrolet'),
('GMC'),
('Dodge'),
('Chrysler'),
('Jeep'),
('Cadillac'),
('Buick'),
('Lincoln'),
('Tesla'),
('Toyota'),
('Honda'),
('Nissan'),
('Mazda'),
('Subaru'),
('Mitsubishi'),
('Lexus'),
('Acura'),
('Infiniti'),
('Hyundai'),
('Kia'),
('Genesis'),
('BMW'),
('Mercedes-Benz'),
('Audi'),
('Volkswagen'),
('Porsche'),
('Volvo'),
('MINI'),
('Fiat'),
('Alfa Romeo')
ON DUPLICATE KEY UPDATE make_name=VALUES(make_name);

INSERT INTO ref_nuisance_category (category_name) VALUES
('Appliances'),
('Vehicles & Vehicle-Related'),
('Scrap & Metal'),
('Construction & Demolition Debris'),
('Furniture & Household Junk'),
('Outdoor & Yard Waste'),
('Trash & Refuse'),
('Hazardous / Environmental'),
('Tents / Temporary Structures'),
('Animals & Related Nuisances')
ON DUPLICATE KEY UPDATE category_name=VALUES(category_name);

INSERT INTO ref_nuisance_item (category_id, item_name)
SELECT category_id, 'Refrigerator / Freezer' AS item_name FROM ref_nuisance_category WHERE category_name='Appliances'
UNION ALL
SELECT category_id, 'Washer' AS item_name FROM ref_nuisance_category WHERE category_name='Appliances'
UNION ALL
SELECT category_id, 'Dryer' AS item_name FROM ref_nuisance_category WHERE category_name='Appliances'
UNION ALL
SELECT category_id, 'Dishwasher' AS item_name FROM ref_nuisance_category WHERE category_name='Appliances'
UNION ALL
SELECT category_id, 'Oven / Stove' AS item_name FROM ref_nuisance_category WHERE category_name='Appliances'
UNION ALL
SELECT category_id, 'Microwave' AS item_name FROM ref_nuisance_category WHERE category_name='Appliances'
UNION ALL
SELECT category_id, 'Water Heater' AS item_name FROM ref_nuisance_category WHERE category_name='Appliances'
UNION ALL
SELECT category_id, 'Furnace / HVAC Unit' AS item_name FROM ref_nuisance_category WHERE category_name='Appliances'
UNION ALL
SELECT category_id, 'Dehumidifier' AS item_name FROM ref_nuisance_category WHERE category_name='Appliances'
UNION ALL
SELECT category_id, 'Air Conditioner (Window or Split)' AS item_name FROM ref_nuisance_category WHERE category_name='Appliances'
UNION ALL
SELECT category_id, 'Vending Machine' AS item_name FROM ref_nuisance_category WHERE category_name='Appliances'
UNION ALL
SELECT category_id, 'Derelict Vehicle' AS item_name FROM ref_nuisance_category WHERE category_name='Vehicles & Vehicle-Related'
UNION ALL
SELECT category_id, 'Non-operational vehicle' AS item_name FROM ref_nuisance_category WHERE category_name='Vehicles & Vehicle-Related'
UNION ALL
SELECT category_id, 'Vehicle without plates' AS item_name FROM ref_nuisance_category WHERE category_name='Vehicles & Vehicle-Related'
UNION ALL
SELECT category_id, 'Vehicle on blocks / missing wheels' AS item_name FROM ref_nuisance_category WHERE category_name='Vehicles & Vehicle-Related'
UNION ALL
SELECT category_id, 'Burned vehicle' AS item_name FROM ref_nuisance_category WHERE category_name='Vehicles & Vehicle-Related'
UNION ALL
SELECT category_id, 'Wrecked vehicle' AS item_name FROM ref_nuisance_category WHERE category_name='Vehicles & Vehicle-Related'
UNION ALL
SELECT category_id, 'Abandoned RV' AS item_name FROM ref_nuisance_category WHERE category_name='Vehicles & Vehicle-Related'
UNION ALL
SELECT category_id, 'Abandoned camper' AS item_name FROM ref_nuisance_category WHERE category_name='Vehicles & Vehicle-Related'
UNION ALL
SELECT category_id, 'Boat on trailer' AS item_name FROM ref_nuisance_category WHERE category_name='Vehicles & Vehicle-Related'
UNION ALL
SELECT category_id, 'ATV / UTV' AS item_name FROM ref_nuisance_category WHERE category_name='Vehicles & Vehicle-Related'
UNION ALL
SELECT category_id, 'Dirt bike / Motorcycle storage' AS item_name FROM ref_nuisance_category WHERE category_name='Vehicles & Vehicle-Related'
UNION ALL
SELECT category_id, 'Trailer (utility / cargo)' AS item_name FROM ref_nuisance_category WHERE category_name='Vehicles & Vehicle-Related'
UNION ALL
SELECT category_id, 'Scrap metal piles' AS item_name FROM ref_nuisance_category WHERE category_name='Scrap & Metal'
UNION ALL
SELECT category_id, 'Sheet metal' AS item_name FROM ref_nuisance_category WHERE category_name='Scrap & Metal'
UNION ALL
SELECT category_id, 'Rebar' AS item_name FROM ref_nuisance_category WHERE category_name='Scrap & Metal'
UNION ALL
SELECT category_id, 'Pipes' AS item_name FROM ref_nuisance_category WHERE category_name='Scrap & Metal'
UNION ALL
SELECT category_id, 'Copper wire' AS item_name FROM ref_nuisance_category WHERE category_name='Scrap & Metal'
UNION ALL
SELECT category_id, 'Engine blocks' AS item_name FROM ref_nuisance_category WHERE category_name='Scrap & Metal'
UNION ALL
SELECT category_id, 'Car parts piles' AS item_name FROM ref_nuisance_category WHERE category_name='Scrap & Metal'
UNION ALL
SELECT category_id, 'Rims / wheels' AS item_name FROM ref_nuisance_category WHERE category_name='Scrap & Metal'
UNION ALL
SELECT category_id, 'Exhaust pipes' AS item_name FROM ref_nuisance_category WHERE category_name='Scrap & Metal'
UNION ALL
SELECT category_id, 'Lumber / wood piles' AS item_name FROM ref_nuisance_category WHERE category_name='Construction & Demolition Debris'
UNION ALL
SELECT category_id, 'Plywood sheets' AS item_name FROM ref_nuisance_category WHERE category_name='Construction & Demolition Debris'
UNION ALL
SELECT category_id, 'Broken pallets' AS item_name FROM ref_nuisance_category WHERE category_name='Construction & Demolition Debris'
UNION ALL
SELECT category_id, 'Drywall' AS item_name FROM ref_nuisance_category WHERE category_name='Construction & Demolition Debris'
UNION ALL
SELECT category_id, 'Concrete chunks' AS item_name FROM ref_nuisance_category WHERE category_name='Construction & Demolition Debris'
UNION ALL
SELECT category_id, 'Bricks' AS item_name FROM ref_nuisance_category WHERE category_name='Construction & Demolition Debris'
UNION ALL
SELECT category_id, 'Cinder blocks' AS item_name FROM ref_nuisance_category WHERE category_name='Construction & Demolition Debris'
UNION ALL
SELECT category_id, 'Roofing shingles' AS item_name FROM ref_nuisance_category WHERE category_name='Construction & Demolition Debris'
UNION ALL
SELECT category_id, 'Windows' AS item_name FROM ref_nuisance_category WHERE category_name='Construction & Demolition Debris'
UNION ALL
SELECT category_id, 'Doors' AS item_name FROM ref_nuisance_category WHERE category_name='Construction & Demolition Debris'
UNION ALL
SELECT category_id, 'Cabinets' AS item_name FROM ref_nuisance_category WHERE category_name='Construction & Demolition Debris'
UNION ALL
SELECT category_id, 'Toilets / sinks / tubs' AS item_name FROM ref_nuisance_category WHERE category_name='Construction & Demolition Debris'
UNION ALL
SELECT category_id, 'Mattresses' AS item_name FROM ref_nuisance_category WHERE category_name='Furniture & Household Junk'
UNION ALL
SELECT category_id, 'Couches / sofas' AS item_name FROM ref_nuisance_category WHERE category_name='Furniture & Household Junk'
UNION ALL
SELECT category_id, 'Chairs' AS item_name FROM ref_nuisance_category WHERE category_name='Furniture & Household Junk'
UNION ALL
SELECT category_id, 'Dressers' AS item_name FROM ref_nuisance_category WHERE category_name='Furniture & Household Junk'
UNION ALL
SELECT category_id, 'Tables' AS item_name FROM ref_nuisance_category WHERE category_name='Furniture & Household Junk'
UNION ALL
SELECT category_id, 'Rugs / carpets' AS item_name FROM ref_nuisance_category WHERE category_name='Furniture & Household Junk'
UNION ALL
SELECT category_id, 'Exercise equipment' AS item_name FROM ref_nuisance_category WHERE category_name='Furniture & Household Junk'
UNION ALL
SELECT category_id, 'Overgrown weeds' AS item_name FROM ref_nuisance_category WHERE category_name='Outdoor & Yard Waste'
UNION ALL
SELECT category_id, 'Dead trees' AS item_name FROM ref_nuisance_category WHERE category_name='Outdoor & Yard Waste'
UNION ALL
SELECT category_id, 'Fallen branches' AS item_name FROM ref_nuisance_category WHERE category_name='Outdoor & Yard Waste'
UNION ALL
SELECT category_id, 'Grass clippings piles' AS item_name FROM ref_nuisance_category WHERE category_name='Outdoor & Yard Waste'
UNION ALL
SELECT category_id, 'Leaves piles' AS item_name FROM ref_nuisance_category WHERE category_name='Outdoor & Yard Waste'
UNION ALL
SELECT category_id, 'Dirt piles' AS item_name FROM ref_nuisance_category WHERE category_name='Outdoor & Yard Waste'
UNION ALL
SELECT category_id, 'Gravel piles' AS item_name FROM ref_nuisance_category WHERE category_name='Outdoor & Yard Waste'
UNION ALL
SELECT category_id, 'Loose garbage bags' AS item_name FROM ref_nuisance_category WHERE category_name='Trash & Refuse'
UNION ALL
SELECT category_id, 'Overflowing trash cans' AS item_name FROM ref_nuisance_category WHERE category_name='Trash & Refuse'
UNION ALL
SELECT category_id, 'Dumped household trash' AS item_name FROM ref_nuisance_category WHERE category_name='Trash & Refuse'
UNION ALL
SELECT category_id, 'Food waste / rotten food' AS item_name FROM ref_nuisance_category WHERE category_name='Trash & Refuse'
UNION ALL
SELECT category_id, 'Used diapers' AS item_name FROM ref_nuisance_category WHERE category_name='Trash & Refuse'
UNION ALL
SELECT category_id, 'Broken glass' AS item_name FROM ref_nuisance_category WHERE category_name='Trash & Refuse'
UNION ALL
SELECT category_id, 'Tires (mosquito hazard)' AS item_name FROM ref_nuisance_category WHERE category_name='Trash & Refuse'
UNION ALL
SELECT category_id, 'Oil drums' AS item_name FROM ref_nuisance_category WHERE category_name='Hazardous / Environmental'
UNION ALL
SELECT category_id, 'Fuel containers' AS item_name FROM ref_nuisance_category WHERE category_name='Hazardous / Environmental'
UNION ALL
SELECT category_id, 'Propane tanks' AS item_name FROM ref_nuisance_category WHERE category_name='Hazardous / Environmental'
UNION ALL
SELECT category_id, 'Paint cans' AS item_name FROM ref_nuisance_category WHERE category_name='Hazardous / Environmental'
UNION ALL
SELECT category_id, 'Batteries (car/industrial)' AS item_name FROM ref_nuisance_category WHERE category_name='Hazardous / Environmental'
UNION ALL
SELECT category_id, 'E-waste piles' AS item_name FROM ref_nuisance_category WHERE category_name='Hazardous / Environmental'
UNION ALL
SELECT category_id, 'Camping tents' AS item_name FROM ref_nuisance_category WHERE category_name='Tents / Temporary Structures'
UNION ALL
SELECT category_id, 'Tarps (ground or vehicle-covered)' AS item_name FROM ref_nuisance_category WHERE category_name='Tents / Temporary Structures'
UNION ALL
SELECT category_id, 'Makeshift shelters' AS item_name FROM ref_nuisance_category WHERE category_name='Tents / Temporary Structures'
UNION ALL
SELECT category_id, 'Storage canopies' AS item_name FROM ref_nuisance_category WHERE category_name='Tents / Temporary Structures'
UNION ALL
SELECT category_id, 'Collapsed carports' AS item_name FROM ref_nuisance_category WHERE category_name='Tents / Temporary Structures'
UNION ALL
SELECT category_id, 'Excessive dog kennels' AS item_name FROM ref_nuisance_category WHERE category_name='Animals & Related Nuisances'
UNION ALL
SELECT category_id, 'Animal feces accumulation' AS item_name FROM ref_nuisance_category WHERE category_name='Animals & Related Nuisances'
UNION ALL
SELECT category_id, 'Dead animals' AS item_name FROM ref_nuisance_category WHERE category_name='Animals & Related Nuisances'
UNION ALL
SELECT category_id, 'Infestations (rats, roaches, raccoons)' AS item_name FROM ref_nuisance_category WHERE category_name='Animals & Related Nuisances'
ON DUPLICATE KEY UPDATE item_name=item_name;

INSERT INTO ref_user_submitted_vehicle_model_status (status_key, status_label) VALUES
('PENDING', 'Pending Admin Review'),
('APPROVED', 'Approved (Merged into Canonical Models)'),
('REJECTED', 'Rejected')
ON DUPLICATE KEY UPDATE status_label=VALUES(status_label);

INSERT INTO ref_email_template (template_key, subject, body_text) VALUES
('complaint_new_comment', 'New comment on your TrashyNeighbors complaint', 'Hello {{screen_name}},

A new comment was posted on your complaint:

Title: {{post_title}}
Comment by: {{comment_author}}

View it here: {{post_url}}

— TrashyNeighbors'),
('complaint_new_update', 'New update on your TrashyNeighbors complaint', 'Hello {{screen_name}},

There is a new update on your complaint:

Title: {{post_title}}

View it here: {{post_url}}

— TrashyNeighbors')
ON DUPLICATE KEY UPDATE subject=VALUES(subject), body_text=VALUES(body_text);

INSERT INTO ref_import_manifest (import_key, priority, source_name, source_url, licensing_note, installer_behavior, tables_target_json, references_json) VALUES
('zip_city_state', 1, 'USPS City State Product (authoritative)', 'https://postalpro.usps.com/address-quality/city-state-product', 'May require USPS agreement. If unavailable, use Census Gazetteer/ZCTA fallback.', 'Download if credentials/approval provided; otherwise fallback to Census-based ZIP approximation.', '["ref_zip_city"]', '["USPS City State Product describes ZIP-to-city/state validation dataset.","Census discusses USPS City State Product usage."]'),
('zip_city_state_fallback', 2, 'US Census Gazetteer / ZCTA references (public fallback)', 'https://www.census.gov/geographies/reference-files/time-series/geo/gazetteer-files.html', 'Public. Not identical to USPS city naming; used as fallback for ZIP/city/state autofill.', 'Download Gazetteer/ZCTA-derived file(s) and populate ZIP->City/State approximations.', '["ref_zip_city"]', '[]'),
('vehicle_make_model_year', 1, 'NHTSA vPIC API (official vehicle product info catalog)', 'https://vpic.nhtsa.dot.gov/api/', 'Public API. Use during install to populate canonical make/model/year tables.', 'For each year range configured, fetch makes then models by year+make (see NHTSA dataset docs). Cache results into MariaDB and index for fast lookup.', '["ref_vehicle_make","ref_vehicle_model","ref_vehicle_model_year"]', '[]')
ON DUPLICATE KEY UPDATE priority=VALUES(priority), source_name=VALUES(source_name), source_url=VALUES(source_url), licensing_note=VALUES(licensing_note), installer_behavior=VALUES(installer_behavior), tables_target_json=VALUES(tables_target_json), references_json=VALUES(references_json);

COMMIT;
SET FOREIGN_KEY_CHECKS=1;
