import time
from machine import I2C, Pin
from machine_i2c_lcd import I2cLcd

# ---------------------------------------------------------------------
# CONFIGURATION DU SYSTÈME
# ---------------------------------------------------------------------
PIN_CORRECT = "1234"      # Code PIN d'accès par défaut
TEMPS_OUVERTURE = 3       # Durée d'activation du solénoïde (en secondes)

# Configuration du Relais (Active HIGH : 0 = Verrouillé, 1 = Déverrouillé)
relais = Pin(16, Pin.OUT, value=0)

# Configuration des LED et du Buzzer
led_verte = Pin(18, Pin.OUT, value=0)
led_rouge = Pin(19, Pin.OUT, value=0)  # Allumée au repos (Porte verrouillée)
buzzer = Pin(4, Pin.OUT, value=0)

# Configuration de l'Écran LCD 16x2 I2C (SDA -> GPIO 21, SCL -> GPIO 22)
I2C_ADDR = 0x27           # Adresse détectée lors du scan
i2c = I2C(0, sda=Pin(21), scl=Pin(22), freq=100000)

# Initialisation de l'écran LCD
lcd = I2cLcd(i2c, I2C_ADDR, 2, 16)

# Configuration du Clavier Matriciel 4x4
KEYPAD = [
    ['1', '2', '3', 'A'],
    ['4', '5', '6', 'B'],
    ['7', '8', '9', 'C'],
    ['*', '0', '#', 'D']
]

# Lignes (Outputs) -> GPIO 12, 13, 14, 27
row_pins = [Pin(12, Pin.OUT), Pin(13, Pin.OUT), Pin(14, Pin.OUT), Pin(27, Pin.OUT)]

# Colonnes (Inputs avec Pull-Down) -> GPIO 26, 25, 33, 32
col_pins = [Pin(26, Pin.IN, Pin.PULL_DOWN), Pin(25, Pin.IN, Pin.PULL_DOWN),
            Pin(33, Pin.IN, Pin.PULL_DOWN), Pin(32, Pin.IN, Pin.PULL_DOWN)]

# ---------------------------------------------------------------------
# FONCTIONS UTILITAIRES ET SIGNAUX
# ---------------------------------------------------------------------
def scan_keypad():
    """Scanne le clavier matriciel et retourne la touche appuyée."""
    for r_idx, r_pin in enumerate(row_pins):
        r_pin.value(1)
        for c_idx, c_pin in enumerate(col_pins):
            if c_pin.value() == 1:
                r_pin.value(0)
                return KEYPAD[r_idx][c_idx]
        r_pin.value(0)
    return None

def afficher_lcd(ligne1, ligne2=""):
    """Formatage et affichage propre sur 2 lignes de 16 caractères."""
    lcd.clear()
    lcd.putstr(ligne1[:16])
    if ligne2:
        lcd.move_to(0, 1)
        lcd.putstr(ligne2[:16])

def reinitialiser_ecran():
    """Affiche l'invite de saisie par défaut et réinitialise les voyants."""
    led_verte.value(0)
    led_rouge.value(0)  # Rouge allumé = Verrouillé
    afficher_lcd("CONTROLE D'ACCES", "Code PIN: ")

def bip_touche():
    """Retour sonore très court lors de la pression d'une touche."""
    buzzer.value(1)
    time.sleep(0.03)
    buzzer.value(0)

def bip_acces_accorde():
    """Double bip court de validation."""
    buzzer.value(1)
    time.sleep(0.1)
    buzzer.value(0)
    time.sleep(0.08)
    buzzer.value(1)
    time.sleep(0.1)
    buzzer.value(0)

def bip_acces_refuse():
    """Bip long d'erreur avec clignotement de la LED rouge."""
    
    # Clignotement rapide rouge pendant l'alerte
    for _ in range(5):
        led_rouge.value(1)
        buzzer.value(1)
        time.sleep(1)
    buzzer.value(1)
    time.sleep(0.1)
    buzzer.value(0)
    time.sleep(0.08)
    buzzer.value(1)
    time.sleep(0.1)
    buzzer.value(0)
        
    
        

# ---------------------------------------------------------------------
# INITIALISATION ET BOUCLE PRINCIPALE
# ---------------------------------------------------------------------
afficher_lcd("   SYSTEME OK   ", " Initialisation ")
time.sleep(1.5)
reinitialiser_ecran()

saisie = ""
last_key = None

while True:
    key = scan_keypad()
    
    if key and key != last_key:
        last_key = key
        bip_touche()  # Bip à chaque touche appuyée
        
        # Touche '*' : Effacer la saisie en cours
        if key == '*':
            saisie = ""
            reinitialiser_ecran()
            
        # Touche '#' : Valider le code entré
        elif key == '#':
            if saisie == PIN_CORRECT:
                # --- ACCÈS ACCORDÉ ---
                led_rouge.value(0)
                led_verte.value(1)
                
                relais.value(1)  # Activer le relais (Déverrouille le solénoïde)
                afficher_lcd(" ACCES ACCORDE! ", " Porte Ouverte ")
                
                bip_acces_accorde()
                
                # Maintien ouvert pendant la durée définie
                time.sleep(TEMPS_OUVERTURE - 0.28)  # Compensation du temps des bips
                
                # Verrouillage automatique
                relais.value(0)  # Désactiver le relais (Verrouille le solénoïde)
                saisie = ""
                reinitialiser_ecran()
            else:
                # --- CODE INCORRECT ---
                relais.value(0)  # Maintient le solénoïde verrouillé
                afficher_lcd(" CODE INCORRECT ", " Accès Refusé ! ")
                
                bip_acces_refuse()
                
                saisie = ""
                reinitialiser_ecran()  
                
        # Saisie d'un chiffre ou d'une lettre (limité à 8 caractères)
        elif len(saisie) < 8:
            saisie += key
            masque = "*" * len(saisie)
            afficher_lcd("CONTROLE D'ACCES", "Code PIN: " + masque)
            
            time.sleep(0.15)  # Anti-rebond du clavier
    elif not key:
        last_key = None
        
    else:
        
      time.sleep(0.02)


