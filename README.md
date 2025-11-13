# 🚗 Drive Exam Autorecorder

This tool automatically registers you for a Ukrainian driving exam at a selected TSC (Territorial Service Center) using your digital signature and user-defined preferences.

---

## 📦 Prerequisites

- Python 3.11.4
- Install dependencies:

```bash
pip install -r requirements.txt
```

---

## ⚙️ Configuration

All settings are managed through the `config.py` file.

| Variable         | Description                                                                                                         |
| ---------------- | ------------------------------------------------------------------------------------------------------------------- |
| **DC**           | Local path to your digital signature file (`.jks`, `.pfx`, `.pk8`, `.zs2`, `.dat`). |
| **PASSWORD**     | Password for the digital signature. |
| **PHONE**        | Ukrainian phone number. |
| **EMAIL**        | Email address where the confirmation ticket will be sent. |
| **VEHICLE**      | Vehicle ownership type — `school` (driving school) or `tsc` (service center). |
| **TRANSMISSION** | Transmission type — `manual` or `automatic`. Optional if the vehicle belongs to a driving school. |
| **DATES**        | Preferred exam dates in `DD.MM` format. Leave empty to select all available dates. |
| **TIME**         | Desired time in `HH:MM` format. If multiple slots are available, the script will pick the one closest to this time. |
| **TSC**          | Number (ID) of the desired service center. |

---

## 🚀 Usage

After configuring your `config.py`, simply run:

```bash
python main.py
```

The script will:

1. Authenticate using your digital signature.
2. Search available slots that match your preferences.
3. Automatically register for the earliest matching driving exam.

---

## 🧩 Notes

- Make sure your digital signature file and password are valid before running the program.
