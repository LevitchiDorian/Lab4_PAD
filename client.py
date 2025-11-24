import requests
import sys
import time
import os

LOAD_BALANCER_URL = os.environ.get("LOAD_BALANCER_URL", "https://lab4pad-production.up.railway.app")
LINE_SEPARATOR = "-" * 70


def print_header():
    print(LINE_SEPARATOR)
    print("  CLIENT CRUD - Sistem cu Load Balancer, 2 Servere & Sincronizare DB")
    print(LINE_SEPARATOR)


def print_menu():
    print("\nAlege o opțiune:")
    print(" 1) Afișează toți angajații")
    print(" 2) Caută angajat după ID")
    print(" 3) Adaugă angajat nou")
    print(" 4) Modifică angajat existent")
    print(" 5) Șterge angajat")
    print(" 0) Ieșire")
    print(LINE_SEPARATOR)


def input_int(prompt):
    while True:
        value = input(prompt).strip()
        if value == "":
            print("[INPUT] Valoare goală. Încearcă din nou.")
            continue
        if not value.isdigit():
            print("[INPUT] Te rog introdu un număr întreg valid.")
            continue
        return int(value)


def input_non_empty(prompt):
    while True:
        value = input(prompt).strip()
        if value == "":
            print("[INPUT] Câmpul nu poate fi gol. Încearcă din nou.")
        else:
            return value


def send_request(method, path, **kwargs):
    """
    Wrapper general peste requests.<method>, cu tratare de erori și afișare DB info.
    """
    url = f"{LOAD_BALANCER_URL}{path}"
    try:
        resp = requests.request(method, url, timeout=5, **kwargs)
    except requests.exceptions.ConnectionError:
        print(f"[EROARE] Nu mă pot conecta la {LOAD_BALANCER_URL}. Verifică load balancer-ul.")
        return None, None
    except requests.exceptions.Timeout:
        print("[EROARE] Timeout la răspuns. Serverul răspunde prea încet.")
        return None, None
    except requests.exceptions.RequestException as e:
        print(f"[EROARE] Eroare la cerere: {e}")
        return None, None

    db_info = resp.headers.get("X-Database-Info", "N/A")
    print(f"\n[SERVER] HTTP {resp.status_code}  |  {db_info}")


    try:
        data = resp.json()
    except ValueError:
        data = None

    if not resp.ok:
       
        if isinstance(data, dict) and "error" in data:
            print(f"[SERVER] Mesaj eroare: {data['error']}")
        else:
            print("[SERVER] Răspuns de eroare (non-JSON sau format necunoscut).")
        return None, resp

    return data, resp


def pretty_print_employees(employees):
    """
    Afișare tabelară a listei de angajați.
    employees: list[dict] cu chei: id, name, position
    """
    if not employees:
        print("Nu există înregistrări în baza de date.")
        return

    # Dacă vine un singur dict, îl transformăm într-o listă
    if isinstance(employees, dict):
        employees = [employees]

    print("\nLista angajaților:")
    print(LINE_SEPARATOR)
    print(f"{'ID':<6} {'Nume':<25} {'Pozitie':<25}")
    print(LINE_SEPARATOR)

    for emp in employees:
        emp_id = emp.get("id", "")
        name = emp.get("name", "")
        position = emp.get("position", "")
        print(f"{str(emp_id):<6} {name:<25} {position:<25}")

    print(LINE_SEPARATOR)



def op_list_all():
    print("\n[OPERAȚIE] GET /employees  - Afișare listă completă")
    data, _ = send_request("GET", "/employees")
    if data is not None:
        pretty_print_employees(data)


def op_get_by_id():
    print("\n[OPERAȚIE] GET /employee/<id>  - Căutare angajat după ID")
    emp_id = input_int("Introdu ID-ul angajatului: ")
    data, _ = send_request("GET", f"/employee/{emp_id}")
    if data is not None:
        pretty_print_employees(data)


def op_add_employee():
    print("\n[OPERAȚIE] POST /employee  - Adăugare angajat nou")
    name = input_non_empty("Nume: ")
    position = input_non_empty("Pozitie: ")

    payload = {"name": name, "position": position}
    data, _ = send_request("POST", "/employee", json=payload)

    if data is not None:
        print("\n[INFO] Angajat creat cu succes:")
        pretty_print_employees(data)


def op_update_employee():
    print("\n[OPERAȚIE] PUT /employee/<id>  - Modificare angajat")
    emp_id = input_int("Introdu ID-ul angajatului de modificat: ")
    name = input_non_empty("Nume nou: ")
    position = input_non_empty("Pozitie nouă: ")

    payload = {"name": name, "position": position}
    data, _ = send_request("PUT", f"/employee/{emp_id}", json=payload)

    if data is not None:
        print("\n[INFO] Angajat modificat cu succes:")
        pretty_print_employees(data)


def op_delete_employee():
    print("\n[OPERAȚIE] DELETE /employee/<id>  - Ștergere angajat")
    emp_id = input_int("Introdu ID-ul angajatului de șters: ")

    confirm = input(f"Ești sigur că vrei să ștergi angajatul cu ID={emp_id}? (da/nu): ").strip().lower()
    if confirm not in ("da", "d", "yes", "y"):
        print("[INFO] Operația de ștergere a fost anulată.")
        return

    data, _ = send_request("DELETE", f"/employee/{emp_id}")
    if data is not None:
        print("\n[INFO] Angajat șters (dacă exista):")
        print(data)




def main():
    print_header()
    session = requests.Session() 

    
    time.sleep(0.5)

    while True:
        print_menu()
        choice = input("Introdu opțiunea: ").strip()

        if choice == "1":
            op_list_all()
        elif choice == "2":
            op_get_by_id()
        elif choice == "3":
            op_add_employee()
        elif choice == "4":
            op_update_employee()
        elif choice == "5":
            op_delete_employee()
        elif choice == "0":
            print("\n[EXIT] Închidere client. La revedere!")
            sys.exit(0)
        else:
            print("[INPUT] Opțiune necunoscută. Încearcă din nou.")


if __name__ == "__main__":
    main()
