import os
import random

random.seed(42)

TRAINING_DIR = "training_data"
FILES_PER_CATEGORY = 200

VENDORS = ["Northwind", "Contoso", "Globex", "Initech", "Umbrella Corp", "Acme",
           "Stellar Traders", "Bluewave Supply", "Cascade Freight", "Ironclad Systems"]
NAMES = ["J. Alvarez", "M. Chen", "R. Osei", "S. Patel", "T. Nguyen",
         "K. Whitfield", "D. Romero", "A. Kowalski", "L. Fontaine", "P. Yamamoto"]


def make_invoice():
    total = round(random.uniform(500, 50000), 2)
    return (f"INVOICE #INV-{random.randint(1000,9999)}\n"
            f"Bill To: {random.choice(VENDORS)} Accounts Payable\n"
            f"Subtotal: {total*0.9:.2f}\nTax: {total*0.1:.2f}\n"
            f"Total Due: {total:.2f}\nPayment Terms: Net {random.choice([15,30,45])}")


def make_po():
    return (f"PURCHASE ORDER #PO-{random.randint(1000,9999)}\n"
            f"Vendor: {random.choice(VENDORS)}\n"
            f"Item: {random.choice(['Office chairs','Laptops','Steel brackets','Cloud credits','Packaging material'])}\n"
            f"Quantity: {random.randint(1,500)} units\n"
            f"Unit Cost: {random.uniform(5,500):.2f}\nAuthorized by: Procurement Dept")


def make_resume():
    return (f"RESUME\nName: {random.choice(NAMES)}\n"
            f"Summary: {random.choice(['Software engineer','Data analyst','Product manager','DevOps engineer'])} "
            f"with {random.randint(1,15)} years experience\n"
            f"Experience: Senior role, {random.choice(VENDORS)} Labs\n"
            f"Education: B.S. Computer Science\n"
            f"Skills: {random.choice(['Python, SQL, AWS','Go, Kafka, Kubernetes','Java, Spring, Docker','React, Node, GraphQL'])}")


def make_policy():
    return (f"POLICY DOCUMENT — {random.choice(['Homeowners','Auto','Health','Travel','Liability'])} Coverage\n"
            f"Policy Ref: POL-{random.randint(1000,9999)}\n"
            f"Effective Date: 2026-0{random.randint(1,9)}-01\n"
            f"Coverage limits and exclusions apply. See section {random.randint(1,9)} for details.")


def make_claim():
    return (f"CLAIM FORM\nPolicy Ref: POL-{random.randint(1000,9999)}\n"
            f"Claimant: {random.choice(NAMES)}\n"
            f"Incident: {random.choice(['Water damage','Vehicle collision','Theft','Fire damage','Storm damage'])}\n"
            f"Estimated Loss: {random.uniform(200,20000):.2f}\nAdjuster Notes: pending review")


def make_other():
    templates = [
        "Meeting notes from the {} planning session covering roadmap items.",
        "Internal memo regarding {} scheduled for next month.",
        "Newsletter summarizing recent {} and team announcements.",
        "General correspondence unrelated to financial or HR processes, re: {}.",
        "Draft agenda for the upcoming {} review.",
    ]
    fillers = ["quarterly", "office relocation", "product updates", "budget planning",
               "team offsite", "vendor onboarding", "policy revision"]
    return random.choice(templates).format(random.choice(fillers))


GENERATORS = {
    "Invoice": make_invoice, "Purchase Order": make_po, "Resume": make_resume,
    "Policy": make_policy, "Claim": make_claim, "Other": make_other,
}


def generate_files():
    for category, gen in GENERATORS.items():
        folder = os.path.join(TRAINING_DIR, category)
        os.makedirs(folder, exist_ok=True)

        for i in range(1, FILES_PER_CATEGORY + 1):
            text = gen()
            filename = f"{category.lower().replace(' ', '_')}_{i:04d}.txt"
            filepath = os.path.join(folder, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(text)

        print(f"{category}: wrote {FILES_PER_CATEGORY} files to {folder}")


if __name__ == "__main__":
    generate_files()
    print(f"\nDone. {FILES_PER_CATEGORY * len(GENERATORS)} files total across "
          f"{len(GENERATORS)} categories in '{TRAINING_DIR}/'")
