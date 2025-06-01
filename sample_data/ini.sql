--users
INSERT INTO users (id, name) VALUES
  ('00000000-0000-0000-0000-000000000001', 'Alice'),
  ('00000000-0000-0000-0000-000000000002', 'Bob'),
  ('00000000-0000-0000-0000-000000000003', 'Charlie'),
  ('00000000-0000-0000-0000-000000000004', 'Dave'),
  ('00000000-0000-0000-0000-000000000005', 'Eve'),
  ('00000000-0000-0000-0000-000000000006', 'Frank');

--currency
INSERT INTO currency (code, name, symbol) VALUES
  ('USD', 'US Dollar', '$'),
  ('PHP', 'Philippine Peso', '₱'),
  ('EUR', 'Euro', '€');
  
--Extra data for reporting
INSERT INTO users (id, name) VALUES
  ('00000000-0000-0000-0000-000000000007','Grace');
INSERT INTO transactions (transaction_id, sender_id, receiver_id, amount, currency, timestamp, status)
VALUES
  ('b1b2b3b4-b5b6-b7b8-b9b0-000000000001','00000000-0000-0000-0000-000000000007','00000000-0000-0000-0000-000000000001',500.00,'USD','2025-05-20T10:00:00Z','completed'),
  ('b1b2b3b4-b5b6-b7b8-b9b0-000000000002','00000000-0000-0000-0000-000000000002','00000000-0000-0000-0000-000000000007',750.00,'USD','2025-05-21T14:00:00Z','completed');
