from faker import Faker
from neo4j import GraphDatabase
import random, uuid
from datetime import datetime, timedelta

fake = Faker('en_IN')

driver = GraphDatabase.driver(
    "neo4j+s://6cb04cfe.databases.neo4j.io",
    auth=("6cb04cfe", "C1x7YXf_3-BbdiNktqVMOUvbXXfZ8LHgwfbDVMnvsPA")
)

INDIAN_CITIES = [
    "Mumbai, Maharashtra", "Delhi, Delhi", "Bengaluru, Karnataka",
    "Hyderabad, Telangana", "Chennai, Tamil Nadu", "Kolkata, West Bengal",
    "Pune, Maharashtra", "Ahmedabad, Gujarat", "Jaipur, Rajasthan",
    "Surat, Gujarat", "Lucknow, Uttar Pradesh", "Kanpur, Uttar Pradesh",
    "Nagpur, Maharashtra", "Indore, Madhya Pradesh", "Thane, Maharashtra",
    "Bhopal, Madhya Pradesh", "Visakhapatnam, Andhra Pradesh", "Patna, Bihar",
    "Vadodara, Gujarat", "Ghaziabad, Uttar Pradesh"
]

def indian_phone():
    first_digit = random.choice(['6', '7', '8', '9'])
    remaining = ''.join([str(random.randint(0, 9)) for _ in range(9)])
    number = first_digit + remaining
    return f"+91-{number[:5]}-{number[5:]}"

def indian_address():
    flat = random.choice(["Flat", "House", "Shop", "Plot", "Block"])
    num  = random.randint(1, 999)
    streets = ["MG Road","Linking Road","Brigade Road","Anna Salai","Park Street","SV Road","Nehru Nagar","Gandhi Colony","Sector 18","Model Town","Vasant Vihar","Koramangala","Andheri West","Bandra East","Whitefield","Indiranagar","Juhu Beach Road","Connaught Place","Karol Bagh","Lajpat Nagar"]
    city = random.choice(INDIAN_CITIES)
    pin  = f"{random.randint(100, 999)}{random.randint(100, 999)}"
    return f"{flat} No. {num}, {random.choice(streets)}, {city} - {pin}"

def make_users(total=510):
    shared_emails    = [fake.email() for _ in range(20)]
    shared_phones    = [indian_phone() for _ in range(20)]
    shared_addresses = [indian_address() for _ in range(15)]
    shared_payments  = [f"card_{random.randint(1000,9999)}" for _ in range(15)]
    users = []
    for i in range(total):
        users.append({
            "id": f"U-{str(i+1).zfill(5)}",
            "name": fake.name(),
            "email":          (random.choice(shared_emails)    if random.random() < 0.3  else fake.email()),
            "phone":          (random.choice(shared_phones)    if random.random() < 0.25 else indian_phone()),
            "address":        (random.choice(shared_addresses) if random.random() < 0.2  else indian_address()),
            "payment_method": (random.choice(shared_payments)  if random.random() < 0.2  else f"card_{random.randint(1000,9999)}")
        })
    return users

def make_transactions(users, total=100000):
    shared_ips     = [fake.ipv4() for _ in range(50)]
    shared_devices = [str(uuid.uuid4())[:8] for _ in range(50)]
    user_ids       = [u["id"] for u in users]
    start          = datetime.now() - timedelta(days=365)
    txs            = []
    for i in range(total):
        sender   = random.choice(user_ids)
        receiver = random.choice([u for u in user_ids if u != sender])
        ip       = (random.choice(shared_ips)     if random.random() < 0.15 else fake.ipv4())
        device   = (random.choice(shared_devices) if random.random() < 0.10 else str(uuid.uuid4())[:8])
        amount   = round(random.uniform(500, 5000000), 2)
        risk = 0.05
        if ip in shared_ips:         risk += 0.4
        if device in shared_devices: risk += 0.3
        if amount > 1000000:         risk += 0.2
        risk   = round(min(risk, 1.0), 2)
        status = ("flagged" if risk > 0.7 else "review" if risk > 0.4 else "clear")
        date   = start + timedelta(seconds=random.randint(0, 365 * 24 * 3600))
        txs.append({
            "id":          f"TX-{str(i+1).zfill(6)}",
            "sender_id":   sender,
            "receiver_id": receiver,
            "amount":      amount,
            "currency":    "INR",
            "timestamp":   date.isoformat(),
            "ip_address":  ip,
            "device_id":   device,
            "status":      status,
            "risk_score":  risk
        })
    return txs

def create_indexes():
    print("Creating indexes...")
    with driver.session() as s:
        s.run("CREATE INDEX user_id_idx IF NOT EXISTS FOR (u:User) ON (u.id)")
        s.run("CREATE INDEX tx_id_idx IF NOT EXISTS FOR (t:Transaction) ON (t.id)")
        s.run("CREATE INDEX tx_ip_idx IF NOT EXISTS FOR (t:Transaction) ON (t.ip_address)")
        s.run("CREATE INDEX tx_device_idx IF NOT EXISTS FOR (t:Transaction) ON (t.device_id)")
        s.run("CREATE INDEX user_email_idx IF NOT EXISTS FOR (u:User) ON (u.email)")
        s.run("CREATE INDEX user_phone_idx IF NOT EXISTS FOR (u:User) ON (u.phone)")
    print("   Indexes ready")

def save_users(users):
    print(f"Saving {len(users)} users...")
    with driver.session() as s:
        for i in range(0, len(users), 500):
            batch = users[i:i+500]
            s.run("UNWIND $batch AS u MERGE (user:User {id: u.id}) SET user += u", batch=batch)
    print(f"  {len(users)} users saved")

def save_transactions(txs):
    print(f"Saving {len(txs)} transactions...")
    with driver.session() as s:
        for i in range(0, len(txs), 500):
            batch = txs[i:i+500]
            s.run("UNWIND $batch AS t MERGE (tx:Transaction {id: t.id}) SET tx += t", batch=batch)
            if i % 10000 == 0:
                print(f"  v {i+len(batch)} transactions saved")
    print(f"  All {len(txs)} transactions saved")

def create_relationships(txs):
    print("Creating graph relationships...")
    tx_ids = [t["id"] for t in txs]

    for rel_name, query in [
        ("INITIATED", """
            UNWIND $ids AS tid
            MATCH (t:Transaction {id: tid})
            MATCH (u:User {id: t.sender_id})
            MERGE (u)-[:INITIATED]->(t)
        """),
        ("RECEIVED", """
            UNWIND $ids AS tid
            MATCH (t:Transaction {id: tid})
            MATCH (u:User {id: t.receiver_id})
            MERGE (u)-[:RECEIVED]->(t)
        """),
        ("SENT", """
            UNWIND $ids AS tid
            MATCH (t:Transaction {id: tid})
            MATCH (s:User {id: t.sender_id})
            MATCH (r:User {id: t.receiver_id})
            MERGE (s)-[:SENT {tx_id: tid}]->(r)
        """),
    ]:
        print(f"  Linking {rel_name}...")
        for i in range(0, len(tx_ids), 1000):
            batch = tx_ids[i:i+1000]
            try:
                with driver.session() as s:
                    s.run(query, ids=batch)
            except Exception as e:
                print(f"    ! Batch {i} error: {e}")
            if i % 20000 == 0:
                print(f"    {i+len(batch)}/{len(tx_ids)}...")
        print(f"     {rel_name} done")

    for rel, prop in [("SHARED_EMAIL","email"),("SHARED_PHONE","phone"),("SHARED_ADDRESS","address"),("SHARED_PAYMENT","payment_method")]:
        print(f"  Linking {rel}...")
        try:
            with driver.session() as s:
                s.run(f"""
                    MATCH (u:User)
                    WITH u.{prop} AS val, collect(u) AS users
                    WHERE size(users) > 1
                    UNWIND users AS a UNWIND users AS b
                    WITH a, b WHERE a.id < b.id
                    MERGE (a)-[:{rel}]->(b)
                """)
            print(f"     {rel} done")
        except Exception as e:
            print(f"    ! {rel} error: {e}")

    print("  Linking SAME_IP (TX->TX)...")
    with driver.session() as s:
        result = s.run("MATCH (t:Transaction) WITH t.ip_address AS ip, count(t) AS cnt WHERE cnt > 1 RETURN ip, cnt ORDER BY cnt ASC")
        shared_ips = [(r["ip"], r["cnt"]) for r in result]
    print(f"    Found {len(shared_ips)} shared IPs...")
    for idx, (ip, cnt) in enumerate(shared_ips):
        try:
            with driver.session() as s:
                s.run("""
                    MATCH (t:Transaction {ip_address: $ip})
                    WITH collect(t.id) AS ids
                    UNWIND ids AS a_id UNWIND ids AS b_id
                    WITH a_id, b_id WHERE a_id < b_id
                    MATCH (a:Transaction {id: a_id}), (b:Transaction {id: b_id})
                    MERGE (a)-[:SAME_IP]->(b)
                """, ip=ip)
        except Exception as e:
            print(f"    ! Skipped IP {ip}: {e}")
        if idx % 10 == 0:
            print(f"    {idx+1}/{len(shared_ips)} IPs done...")
    print("    SAME_IP done")

    print("  Linking SAME_DEVICE (TX->TX)...")
    with driver.session() as s:
        result = s.run("MATCH (t:Transaction) WITH t.device_id AS device, count(t) AS cnt WHERE cnt > 1 RETURN device, cnt ORDER BY cnt ASC")
        shared_devices = [(r["device"], r["cnt"]) for r in result]
    print(f"    Found {len(shared_devices)} shared devices...")
    for idx, (device, cnt) in enumerate(shared_devices):
        try:
            with driver.session() as s:
                s.run("""
                    MATCH (t:Transaction {device_id: $device})
                    WITH collect(t.id) AS ids
                    UNWIND ids AS a_id UNWIND ids AS b_id
                    WITH a_id, b_id WHERE a_id < b_id
                    MATCH (a:Transaction {id: a_id}), (b:Transaction {id: b_id})
                    MERGE (a)-[:SAME_DEVICE]->(b)
                """, device=device)
        except Exception as e:
            print(f"    ! Skipped device {device}: {e}")
        if idx % 10 == 0:
            print(f"    {idx+1}/{len(shared_devices)} devices done...")
    print("    SAME_DEVICE done")
    print("\n  All relationships created!")

if __name__ == "__main__":
    print("Starting FRAML seed data generation...\n")
    create_indexes()
    users = make_users(510)
    txs   = make_transactions(users, 100000)
    save_users(users)
    save_transactions(txs)
    create_relationships(txs)
    driver.close()
    print("\nv Database is ready! 510 users and 100,000 transactions loaded.")