import time
import math
import sys
from gpiozero import Servo, Button

# --- CONFIGURATION MATERIELLE ---
servo_pins = [17, 27, 22, 18]
my_servos = []

# Boutons (Pins Physiques 3, 5, 7 -> GPIO 2, 3, 4)
btn_happy   = Button(2)
btn_neutral = Button(3)
btn_sad     = Button(4)

# --- PARAMETRES DE MOUVEMENT ---
# On ajoute 'current_wave' pour gérer la rigidité
SMOOTHING = 0.05

current_amp = 0.0   # Amplitude (Grandeur du mouvement)
current_speed = 0.0 # Vitesse
current_wave = 0.0  # Ondulation (0 = Bâton, 0.3 = Serpent)

current_emotion = "DEMARRAGE"

# --- FONCTIONS UTILES ---
def log(message):
    print(f"[LOG] {message}")
    sys.stdout.flush()

def lerp(current, target, factor):
    """Transition douce entre deux valeurs"""
    return current + (target - current) * factor

# --- INITIALISATION ---
def sequence_initialisation():
    log("--- INITIALISATION ---")
    for p in servo_pins:
        try:
            s = Servo(p)
            my_servos.append(s)
        except Exception:
            pass 
            
    # Petit check-up visuel
    for s in my_servos: s.value = 0
    time.sleep(0.5)
    log("Pret.")

# --- MOTEUR PHYSIQUE (C'est ici que la magie opère) ---
def update_tail(amplitude, speed, wave_factor):
    """
    amplitude : force du mouvement
    speed : vitesse du temps
    wave_factor : 0 = Bâton rigide | 0.2+ = Serpent souple
    """
    if speed > 0:
        t = time.time() * speed
        for i, s in enumerate(my_servos):
            # Si wave_factor est 0, l'offset est 0 pour tout le monde -> Synchronisé
            # Si wave_factor est 0.2, chaque moteur est décalé -> Sinusoïdal
            offset = i * wave_factor 
            
            val = math.sin(t - offset) * amplitude
            s.value = max(-1, min(1, val))
    else:
        for s in my_servos: s.value = 0.0

# --- BOUCLE PRINCIPALE ---
try:
    sequence_initialisation()
    
    # Valeurs par défaut (Neutre)
    target_amp = 0.4
    target_speed = 3.0
    target_wave = 0.2 # Par défaut, on ondule (Serpent)
    
    log("En attente...")

    while True:
        # --- CHOIX DE L'EMOTION ---
        
        if btn_happy.is_pressed:
            # JOIE : BÂTON RIGIDE + VITESSE MAX
            # On met le wave à 0.0 pour synchroniser les moteurs
            target_amp = 0.95
            target_speed = 15.0
            target_wave = -0.05 # Légèrement négatif ou 0 pour rigidifier totalement
            
            if current_emotion != "HAPPY":
                log("!!! MODE HAPPY (BATON RIGIDE) !!!")
                current_emotion = "HAPPY"
                
        elif btn_neutral.is_pressed:
            # NEUTRE : SERPENT FLUIDE
            # On met le wave à 0.2 pour un bel effet de vague
            target_amp = 0.4
            target_speed = 3.0
            target_wave = 0.25
            
            if current_emotion != "NEUTRE":
                log("Mode Neutre (Ondulation)")
                current_emotion = "NEUTRE"
                
        elif btn_sad.is_pressed:
            # TRISTE : SERPENT MOU
            # Vague très légère
            target_amp = 0.1
            target_speed = 0.5
            target_wave = 0.3
            
            if current_emotion != "TRISTE":
                log("Mode Triste")
                current_emotion = "TRISTE"

        # --- LISSAGE DES 3 VALEURS ---
        current_amp = lerp(current_amp, target_amp, SMOOTHING)
        current_speed = lerp(current_speed, target_speed, SMOOTHING)
        
        # On lisse aussi le passage Bâton <-> Serpent !
        current_wave = lerp(current_wave, target_wave, SMOOTHING)
        
        # Envoi au moteur physique
        update_tail(current_amp, current_speed, current_wave)
        
        time.sleep(0.01)

except KeyboardInterrupt:
    for s in my_servos: s.value = None