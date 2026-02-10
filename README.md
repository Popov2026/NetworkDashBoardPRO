# NetworkDashBoardPRO
Outil d'administration reseau permettant d'ajouter des periphériques reseau apres un scan ARP, puis d'y associer raccourcis WOL UNC RDP URL
🚀 Network Dashboard Pro v1.1


Network Dashboard Pro est un outil d'administration réseau léger et puissant développé en Python GRATUIT. 
Il permet de centraliser la gestion de vos équipements réseau, d'effectuer des scans de plage IP, et de lancer des actions rapides (WOL, RDP, UNC, HTTP) via une interface intuitive.

✨ Caractéristiques principales:

🖥️ Gestion des ÉquipementsAjout Manuel & Scan : Ajoutez des appareils manuellement ou via le scanner de plage IP intégré.
Formatage MAC Intelligent : Saisie assistée avec ajout automatique des deux-points (:) lors de la frappe.
Tri Dynamique : Classez vos appareils par adresse IP (tri numérique réel) ou par nom au sein de chaque catégorie.
Organisation par Catégories : Regroupez vos équipements et gérez l'ordre d'affichage des groupes grâce à un système d'indexation.

🛠️ Outils d'Administration (Accès Rapide)Chaque appareil bénéficie de raccourcis configurables:
UNC : Accès direct aux partages réseaux (ex: \\192.168.1.10\c$).
URL : Ouverture de l'interface d'administration Web (HTTP/HTTPS).
WOL (Wake-On-Lan) : Réveil à distance avec configuration personnalisable du port et du nombre de paquets magiques.
RDP (MSTSC) : Connexion bureau à distance avec support d'arguments personnalisés.

🛰️ Surveillance & DiagnosticAuto-Ping :

Surveillance en temps réel de l'état (Online/Offline) des appareils avec indicateur visuel coloré (Vert/Rouge).
Scanner ARP : Identification des adresses MAC et résolution des noms d'hôtes (DNS) pendant le scan.

🖱️ Utilisation des Menus Contextuels
Le dashboard utilise intensivement le clic-droit pour éviter d'encombrer l'interface :CibleAction (Clic-Droit)
Nom de Catégorie
Modifier l'ordre (Index), configurer les outils par défaut ou supprimer.Nom d'AppareilRenommer, déplacer vers une autre catégorie ou personnaliser ses outils.Boutons Outils
Configurer les chemins spécifiques (Dossier UNC, URL spécifique, arguments RDP).

📂 Structure des Données :

L'application sépare les données techniques des préférences utilisateur pour plus de flexibilité:
config_reseau_pro_v11.json : Contient la liste des catégories, des appareils et leurs configurations spécifiques.
settings_pro.json : Sauvegarde automatiquement vos réglages (IP de départ, état du ping, dernière catégorie utilisée).

🛠️ Installation & PrérequisPython 3.x installé.Aucune dépendance externe requise (utilise uniquement les bibliothèques standards tkinter, json, subprocess, etc.).
Lancez simplement le script :Bash python wol14.pyw

📝 Import / Export

Import JSON : 
Restaurez facilement une configuration complète depuis un fichier JSON.

Export TXT : 
Générez un rapport texte simple de votre inventaire réseau.

En vous souhaitant une bonne administration, 
Développé par Popov & Gemini - ©2026.
