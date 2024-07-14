from flask import Flask,g, render_template, request, jsonify, flash, redirect, url_for,session
import sqlite_utils
from flask_session import Session
import sqlite3
from datetime import datetime
import logging
import bcrypt
import hashlib
import json


app = Flask(__name__)
app.config['SECRET_KEY'] = 'mina'
app.config['SESSION_TYPE'] = 'filesystem'  # Choisissez un type de stockage pour les sessions (ici, stockage dans le système de fichiers)
Session(app)
DATABASE = 'promotion.db'
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        print("connexion réussie")
    return db

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email:
            flash('Veuillez saisir votre adresse e-mail.', 'error')
            return redirect(url_for('login'))
        if not password:
            flash('Veuillez saisir votre mot de passe.', 'error')
            return redirect(url_for('login'))
        # Rechercher l'utilisateur dans la base de données
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT email,password FROM USER WHERE email=?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user is None:
            flash('Adresse e-mail incorrecte. Veuillez réessayer.', 'error')
            return redirect(url_for('login'))

        if password != user[1]:  
          flash('Mot de passe incorrect. Veuillez réessayer.', 'error')
          return redirect(url_for('login'))
        session['logged_in'] = True
        session['email'] = user[0]  # Remplacez par le bon index pour l'e-mail
        session['password'] = password  # Assurez-vous que vous avez la variable matricule disponible
        return redirect(url_for('menu'))
        # Authentification réussie, rediriger vers une page appropriée

    return render_template('index.html')

@app.route('/menu')
def menu():
    if 'logged_in' in session and session['logged_in']:
        email = session['email']
        password = session['password']
        return render_template('menu.html', email=email, password=password)
    else:
        return redirect(url_for('login'))

    
@app.route('/criteres_selection', methods=['GET', 'POST'])
def criteres_selection():
    if request.method == 'POST':
        try:
            donnees = request.get_json()
            
            # Vérifier que des données ont été reçues
            if not donnees:
                return jsonify({'message': 'Aucune donnée reçue.'}), 400

            # Ouvrir la connexion à la base de données
            conn = get_db()

            # Vider la table avant d'ajouter de nouvelles données
            cursor = conn.cursor()
            cursor.execute("DELETE FROM criteres_selection")
            conn.commit()

            # Insérer les nouvelles données dans la table
            for enregistrement in donnees:
                libelle_grade = enregistrement['libelle_grade']
                annee_selection = enregistrement['annee_selection']
                quota = enregistrement['quota']

                cursor = conn.cursor()
                cursor.execute("INSERT INTO criteres_selection (libelle_grade, annee_selection, quota) VALUES (?, ?, ?)",
                              (libelle_grade, annee_selection, quota))
                conn.commit()

            # Fermer la connexion à la base de données
            conn.close()

            # Rediriger pour afficher les données
            return jsonify({'message': 'Données enregistrées avec succès.'}), 201

        except Exception as e:
            print(f'Erreur lors de l\'enregistrement des données : {e}')
            return jsonify({'message': 'Erreur lors de l\'enregistrement des données.'}), 500

    else:
        # Code pour récupérer les données depuis la base de données et les renvoyer au frontend
        techniciens = get_grades()

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT libelle_grade, annee_selection, quota FROM criteres_selection")
        rows = cursor.fetchall()
        conn.close()

        data = []
        for row in rows:
            enregistrement = {
                'libelle_grade': row[0],
                'annee_selection': row[1],
                'quota': row[2]
            }
            data.append(enregistrement)

        return render_template('criteres_selection.html', techniciens=techniciens, donnees=data)


@app.route('/criteres_selection', methods=['DELETE'])
def supprimer_ligne():
    data = request.get_json()
    libelle_grade = data.get('libelle_grade')
    print("Libellé received from client:", libelle_grade)

    # Supprimer la ligne de la base de données en utilisant le libellé comme identifiant
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("DELETE FROM criteres_selection WHERE libelle_grade=?", (libelle_grade,))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Ligne supprimée avec succès'})

@app.route('/parametrage_diplome')
def parametrage_diplome():
    # Récupérer les techniciens depuis la base de données
    techniciens = get_diplome()
    return render_template('parametrage_diplome.html', techniciens=techniciens)

@app.route('/parametrage_diplome', methods=['POST'])
def enregistrer_diplome():
        # Get the form data from the request
        diplome = request.form.get('liste')
        coefficient = request.form.get('nom1')

    
        # Check if both fields have values
        if not diplome or not coefficient:
            flash('Veuillez remplir tous les champs.', 'error')  # Message flash d'erreur
            return jsonify({'message': 'Veuillez remplir tous les champs.'}), 400

        try:
            # Ouvrir la connexion à la base de données
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT diplome FROM parametrage_diplome WHERE diplome = ?", (diplome,))
            existing_function = cursor.fetchone()

            if existing_function:
                conn.close()
                flash('Le diplome est déjà parametrée.', 'error')  # Message flash d'erreur
                return redirect(url_for('parametrage_fonction'))
            cursor.execute("INSERT INTO parametrage_diplome (diplome,coefficient) VALUES (?, ?)",
                            (diplome,coefficient))
            conn.commit()
            note_diplome()
            # Fermer la connexion à la base de données
            conn.close()
            flash('Diplome ajouté avec succès!', 'success')  # Message flash de succès
            return redirect(url_for('parametrage_diplome'))
        except Exception as e:
            print(f'Erreur lors de l\'enregistrement des données : {e}')
            flash('Erreur lors de l\'enregistrement des données.', 'error')  # Message flash d'erreur
            return jsonify({'message': 'Erreur lors de l\'enregistrement des données.'}), 500


@app.route('/parametrage_fonction')
def parametrage_fonction():
     # Récupérer les techniciens depuis la base de données
    techniciens = get_fonction()
    return render_template('parametrage_fonction.html', techniciens=techniciens)



@app.route('/parametrage_fonction', methods=['POST'])
def enregistrer_fonction():
    try:
        # Get the form data from the request
        fonction = request.form.get('liste')
        coefficient = request.form.get('nom1')
    
        # Check if both fields have values
        if not fonction or not coefficient:
            flash('Veuillez remplir tous les champs.', 'error')  # Message flash d'erreur
            return redirect(url_for('parametrage_fonction'))

        # Ouvrir la connexion à la base de données
        conn = get_db()
        cursor = conn.cursor()

        # Vérifier si la fonction existe déjà
        cursor.execute("SELECT fonction FROM parametrage_fonction WHERE fonction = ?", (fonction,))
        existing_function = cursor.fetchone()

        if existing_function:
            conn.close()
            flash('La fonction est déjà parametrée.', 'error')  # Message flash d'erreur
            return redirect(url_for('parametrage_fonction'))

        # Insérer dans la table parametrage_fonction
        cursor.execute("INSERT INTO parametrage_fonction (fonction, coefficient) VALUES (?, ?)",
                       (fonction, coefficient))

        conn.commit()
        note_fonction()
        # Fermer la connexion à la base de données
        conn.close()
        flash('Fonction ajoutée avec succès!', 'success')  # Message flash de succès
        return redirect(url_for('parametrage_fonction'))
    except Exception as e:
        print(f'Erreur lors de l\'enregistrement des données : {e}')
        flash('Erreur lors de l\'enregistrement des données.', 'error')  # Message flash d'erreur
        return jsonify({'message': 'Erreur lors de l\'enregistrement des données.'}), 500

@app.route('/creer_session', methods=['GET', 'POST'])
def creer_session():
    if request.method == 'POST':
        # Get the form data from the request
        grade = request.form.get('liste')
        session = request.form.get('nom1')
        
    
        # Check if both fields have values
        if not session or not grade:
            flash('Veuillez remplir tous les champs.', 'error')  # Message flash d'erreur
            return redirect(url_for('creer_session'))

        try:
            # Ouvrir la connexion à la base de données
            conn = get_db()
            cursor = conn.cursor()

            # Vérifier si la session existe déjà pour ce grade
            cursor.execute("SELECT id_session FROM session WHERE grade = ? AND date_session = ?", (grade, session))
            existing_session = cursor.fetchone()

            if existing_session:
                flash('Une session pour ce grade et cette date existe déjà.', 'error')  # Message flash d'erreur
                return redirect(url_for('creer_session'))

            # Insérer la nouvelle session
            cursor.execute("INSERT INTO session (grade,date_session) VALUES (?, ?)",
                            (grade, session))
            conn.commit()

            # Fermer la connexion à la base de données
            conn.close()

            # Appeler la fonction moyenne_notes avec l'ID de session
            session_id = cursor.lastrowid  # Récupérer l'ID de la session nouvellement insérée
            moyenne_notes(session_id)
            calculate_final_notes()
            insert_session_agent(session_id,grade)
            
            flash('Session créée avec succès!', 'success')  # Message flash de succès
            return redirect(url_for('creer_session'))
            
        except Exception as e:
            print(f'Erreur lors de l\'enregistrement des données : {e}')
            flash('Erreur lors de l\'enregistrement des données.', 'error')  # Message flash d'erreur
            return redirect(url_for('creer_session'))
    else:
        # Récupérer les techniciens depuis la base de données
        techniciens = get_grade()
        return render_template('creer_session.html', techniciens=techniciens)




@app.route('/liste_exc', methods=['GET', 'POST'])
def liste_exc():
    if request.method == 'POST':
        # Get the form data from the request
        grade = request.form.get('liste')
        liste = request.form.get('nom1')
        
    
        # Check if both fields have values
        if not liste or not grade:
            return jsonify({'message': 'Veuillez remplir tous les champs.'}), 400

        try:
            # Ouvrir la connexion à la base de données
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO liste_exc (libelle_grade,date) VALUES (?, ?)",
                            (grade, liste))
            conn.commit()
            cursor.execute("""
                SELECT G.code_categorie, G.code_corps, G.code_cadre, G.code_grade, G.libelle_grade
                FROM LISTE_EXC S
                JOIN GRADES G ON S.libelle_grade = G.libelle_grade
                WHERE S.libelle_grade = G.libelle_grade
            """, )

            results = cursor.fetchall()

            for result in results:
                code_categorie, code_corps, code_cadre, code_grade, libelle_grade = result

                update_query = '''
                    UPDATE "liste_exc"
                    SET code_categorie = ?,
                        code_corps = ?,
                        code_cadre = ?,
                        code_grade = ?
                    WHERE libelle_grade = ? 
                '''

                cursor.execute(update_query, (code_categorie, code_corps, code_cadre, code_grade, libelle_grade))
                conn.commit()
                insert_liste_exc(grade)

            # Fermer la connexion à la base de données
            conn.close()

            return redirect(url_for('afficher_liste_exc', grade=grade))
            
        except Exception as e:
            print(f'Erreur lors de l\'enregistrement des données : {e}')
            return jsonify({'message': 'Erreur lors de l\'enregistrement des données.'}), 500
    else:
        # Récupérer les techniciens depuis la base de données
        techniciens = get_grade()
        return render_template('liste_exc.html', techniciens=techniciens)



@app.route('/sessions')
def sessions():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id_session,grade,date_session FROM session")
    rows = cursor.fetchall()
    conn.close()
    data = []
    for row in rows:
        enregistrement = {
            'id_session': row[0],
            'grade': row[1],
            'date_session': row[2]
        }
        data.append(enregistrement)
    return render_template('sessions.html', donnees=data)


@app.route('/liste/<int:id_session>')
def liste(id_session):
    conn = get_db()
    cursor = conn.cursor()

    current_year = datetime.now().year  # Get the current year
    sql_query = """
    SELECT 
        A.nom, 
        A.prenom, 
        A.matricule, 
        R.note_finale AS note, 
        SA.statut,
        S.grade
    FROM 
        AGENT A
    INNER JOIN 
        session_agent SA ON A.matricule = SA.matricule 
    INNER JOIN 
        resultat R ON A.matricule = R.matricule 
    INNER JOIN 
        session S ON SA.id_session = S.id_session 
    INNER JOIN 
        GRADES G ON A.code_categorie = G.code_categorie 
                AND A.code_corps = G.code_corps 
                AND A.code_cadre = G.code_cadre 
                AND A.code_grade = G.code_grade 
    INNER JOIN 
        criteres_selection C ON A.code_categorie = C.code_categorie 
                AND A.code_corps = C.code_corps 
                AND A.code_cadre = C.code_cadre 
                AND A.code_grade = C.code_grade             
    WHERE 
        SA.id_session = ? 
        AND G.libelle_grade = S.grade
        AND (? - CAST(SUBSTR(A.date_anc_administration, 7, 4) AS INTEGER)) >= C.annee_selection
    ORDER BY 
        R.note_finale DESC;
    """
    cursor.execute(sql_query, (id_session, current_year))
    rows = cursor.fetchall()
    conn.close()

    data = []
    for idx, row in enumerate(rows):
        grade = row[5]  # Assuming the grade is in the 6th position
        quota = recuperer_quota(grade)

        threshold_idx = int(len(rows) * quota)  # Calculate the threshold index
        is_promoted = idx < threshold_idx 
        enregistrement = {
            'nom': row[0],
            'prenom': row[1],
            'matricule': row[2],
            'note': row[3],
            'statut': 'promu' if is_promoted else 'non promu'
        }
        data.append(enregistrement)
    return render_template('liste.html', donnees=data)



@app.route('/afficher_liste_exc/<grade>', methods=['GET'])
def afficher_liste_exc(grade):
    conn = get_db()
    cursor = conn.cursor()
    
    # Modifiez la requête SQL pour filtrer les agents par grade
    sql_query = """
    SELECT 
        le.libelle_grade, ae.matricule, a.nom, a.prenom, ae.date_anc_grade FROM AGENTS_EXCEPTION ae
    INNER JOIN 
         AGENT a ON ae.matricule = a.matricule
    INNER JOIN 
         liste_exc le ON a.code_categorie = le.code_categorie AND a.code_corps = le.code_corps AND a.code_cadre = le.code_cadre AND a.code_grade = le.code_grade            
    INNER JOIN 
         grades G ON G.code_categorie = le.code_categorie AND G.code_corps = le.code_corps AND G.code_cadre = le.code_cadre AND G.code_grade = le.code_grade 
    WHERE 
      le.libelle_grade = ?
    """
    
    cursor.execute(sql_query, (grade,))
    rows = cursor.fetchall()
    conn.close()

    data = []
    for row in rows:
        enregistrement = {
            'grade': row[0],
            'matricule': row[1],
            'nom': row[2],
            'prenom': row[3],
            'anc_grade': row[4]
        }
        data.append(enregistrement)
        
    return render_template('afficher_liste_exc.html', donnees=data)


def recuperer_coefficient_diplome(diplome):
    # Connexion à la base de données
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Requête SELECT pour récupérer le coefficient du grade de l'agent
    cursor.execute("SELECT coefficient FROM parametrage_diplome WHERE diplome = ?", (diplome,))
    result = cursor.fetchone()  # Récupérer la première ligne de résultat

    # Fermer la connexion à la base de données
    conn.close()

    # Vérifier si le coefficient a été trouvé pour le grade donné
    if result is not None:
        coefficient_diplome = result[0]
        return coefficient_diplome
    else:
        # Ici, nous retournons None si le grade n'est pas trouvé.
        return None

def recuperer_coefficient_fonction(fonction):
    # Connexion à la base de données
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Requête SELECT pour récupérer le coefficient de la fonction de l'agent
    cursor.execute("SELECT coefficient FROM parametrage_fonction WHERE fonction = ?", (fonction,))
    result = cursor.fetchone()  # Récupérer la première ligne de résultat

    # Fermer la connexion à la base de données
    conn.close()

    # Vérifier si le coefficient a été trouvé pour la fonction donnée
    if result is not None:
        coefficient_fonction = result[0]
        return coefficient_fonction
    else:
        # Ici, nous retournons None si la fonction n'est pas trouvée.
        return None

def recuperer_quota(grade):
    # Connexion à la base de données
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Requête SELECT pour récupérer le coefficient de la fonction de l'agent
    cursor.execute("SELECT quota FROM criteres_selection WHERE libelle_grade = ?", (grade,))
    quota_tuple = cursor.fetchone()  # Fetch the tuple
    if quota_tuple:
        quota = quota_tuple[0] / 100  # Divide by 100 to get the quota as a decimal
    else:
        quota = 0  # Default value if the grade is not found

    conn.close()
    return quota
    
 

def calculate_final_notes():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("SELECT matricule FROM resultat")
    matricules = cursor.fetchall()

    final_notes = []

    for matricule in matricules:
        note = calculate_single_final_note(matricule[0], cursor)
        final_notes.append((matricule[0], note))
        note_finale = round(note, 2)

        cursor.execute("UPDATE resultat SET note_finale = ? WHERE matricule = ?", (note_finale, matricule[0]))
        conn.commit()    
    conn.close()

    

def calculate_single_final_note(matricule, cursor):
    cursor.execute("SELECT moyenne_note, calcul_anc_grade, calcul_anc_administration, note_diplome, note_fonction FROM resultat WHERE matricule = ?", (matricule,))
    row = cursor.fetchone()

    if row is None:
        return None

    moyenne_note, calcul_anc_grade, calcul_anc_administration, note_diplome, note_fonction = row

    moyenne_note = moyenne_note or 0
    calcul_anc_grade = calcul_anc_grade or 0
    calcul_anc_administration = calcul_anc_administration or 0
    note_diplome = note_diplome or 0
    note_fonction = note_fonction or 0

    note_finale = (moyenne_note + calcul_anc_grade + calcul_anc_administration + note_diplome + note_fonction)/2.2

    return note_finale

def insert_session_agent(id_session, grade):
    with app.app_context():
        conn = get_db()
        cursor = conn.cursor()

        # Sélectionner les matricules des agents ayant le grade spécifié
        cursor.execute("SELECT AGENT.matricule FROM AGENT JOIN GRADES ON AGENT.code_categorie = GRADES.code_categorie AND AGENT.code_corps = GRADES.code_corps AND AGENT.code_cadre = GRADES.code_cadre AND AGENT.code_grade = GRADES.code_grade WHERE GRADES.libelle_grade = ? AND AGENT.date_anc_grade < '8'", (grade,))
        matricules = cursor.fetchall()
        for matricule in matricules:
            matricule = matricule[0]  # Extraire le matricule du tuple

            # Insérer l'enregistrement dans la table session_agent
            cursor.execute("INSERT INTO session_agent (id_session, matricule) VALUES (?, ?)", (id_session, matricule))

        conn.commit()
        conn.close()
def get_grades():
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        sql = "SELECT libelle_grade FROM grades  "
        cursor.execute(sql)

        resultats = cursor.fetchall()
        cursor.close()
        conn.close()

        techniciens = [resultat[0] for resultat in resultats]
        return techniciens

    except Exception as e:
        print("Erreur lors de l'exécution de la requête SQL :", e)
        return []
       
def get_grade():
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        sql = "SELECT libelle_grade FROM criteres_selection  "
        cursor.execute(sql)

        resultats = cursor.fetchall()

        cursor.close()
        conn.close()

        techniciens = [resultat[0] for resultat in resultats]
        return techniciens

    except Exception as e:
        print("Erreur lors de l'exécution de la requête SQL :", e)
        return []

def get_fonction():
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        sql = "SELECT libelle_fonction FROM fonction  "
        cursor.execute(sql)

        resultats = cursor.fetchall()

        cursor.close()
        conn.close()

        techniciens = [resultat[0] for resultat in resultats]
        return techniciens

    except Exception as e:
        print("Erreur lors de l'exécution de la requête SQL :", e)
        return []

#NOTE_FONCTION:
def note_fonction():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    # Sélectionner les libellés de fonction à partir de parametrage_fonction
    cursor.execute("SELECT DISTINCT fonction FROM parametrage_fonction")
    libelles = cursor.fetchall()
    
    for libelle in libelles:
        libelle_fonction = libelle[0]
        
        # Chercher le code de fonction à partir de la table fonction
        cursor.execute("SELECT code_fonction FROM FONCTION WHERE libelle_fonction = ?", (libelle_fonction,))
        result = cursor.fetchone()
        
        if result:
            code_fonction = result[0]
            
            # Chercher les matricules des agents ayant ce code de fonction
            cursor.execute("SELECT matricule FROM AGENT WHERE code_fonction LIKE ?", ('%' + code_fonction + '%',))
            matricules = cursor.fetchall()
            
            # Chercher le coefficient à partir de parametrage_fonction
            cursor.execute("SELECT coefficient FROM parametrage_fonction WHERE fonction = ?", (libelle_fonction,))
            coefficient = cursor.fetchone()[0]
            
            
            # Mettre à jour la note_fonction dans la table resultat pour chaque agent
            for matricule in matricules:
                cursor.execute("UPDATE resultat SET note_fonction = ? WHERE matricule = ?", (coefficient, matricule[0]))
            
            conn.commit()
#NOTE_DIPLOME:
def note_diplome():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    # Sélectionner les libellés de fonction à partir de parametrage_fonction
    cursor.execute("SELECT DISTINCT diplome FROM parametrage_diplome")
    libelles = cursor.fetchall()
    
    for libelle in libelles:
        libelle_diplome = libelle[0]
        
        # Chercher le code de fonction à partir de la table fonction
        cursor.execute("SELECT code_diplome FROM diplome WHERE libelle_diplome = ?", (libelle_diplome,))
        result = cursor.fetchone()
        
        if result:
            code_diplome = result[0]
            
            # Chercher les matricules des agents ayant ce code de fonction
            cursor.execute("SELECT matricule FROM DIPLOME_AGENT WHERE code_diplome LIKE ?", (code_diplome,))
            matricules = cursor.fetchall()
            
            # Chercher le coefficient à partir de parametrage_fonction
            cursor.execute("SELECT coefficient FROM parametrage_diplome WHERE diplome = ?", (libelle_diplome,))
            coefficient = cursor.fetchone()[0]
            
            # Mettre à jour la note_fonction dans la table resultat pour chaque agent
            for matricule in matricules:
                cursor.execute("UPDATE resultat SET note_diplome = ? WHERE matricule = ?", (coefficient, matricule[0]))
            
            conn.commit()

# MOYENNEEE :
def moyenne_notes(session_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT G.code_categorie, G.code_corps, G.code_cadre, G.code_grade, G.libelle_grade
        FROM session S
        JOIN GRADES G ON S.grade = G.libelle_grade
        WHERE S.id_session = ?
    """, (session_id,))

    results = cursor.fetchall()

    for result in results:
        code_categorie, code_corps, code_cadre, code_grade, libelle_grade = result

        update_query = '''
            UPDATE "criteres_selection"
            SET code_categorie = ?,
                code_corps = ?,
                code_cadre = ?,
                code_grade = ?
            WHERE libelle_grade = ? 
        '''

        cursor.execute(update_query, (code_categorie, code_corps, code_cadre, code_grade, libelle_grade))
        conn.commit()

        query = '''
            SELECT matricule
            FROM "AGENT"
            WHERE code_categorie = ? AND code_corps = ? AND code_cadre = ? AND code_grade = ?
        '''

        cursor.execute(query, (code_categorie, code_corps, code_cadre, code_grade))
        agents = cursor.fetchall()

        cursor.execute("SELECT annee_selection FROM criteres_selection WHERE code_categorie = ? AND code_corps = ? AND code_cadre = ? AND code_grade = ?", (code_categorie, code_corps, code_cadre, code_grade))
        annee = cursor.fetchone()[0]

        cursor.execute("SELECT date_session FROM session WHERE id_session = ?", (session_id,))
        date_session = cursor.fetchone()[0]
        date_obj = datetime.strptime(date_session, "%m/%d/%Y")
        year = date_obj.year
        notes_query = '''
            SELECT note
            FROM "NOTES_AGENT"
        WHERE matricule = ? AND code_exerc >= ? AND code_exerc <= ?
        '''

        notes = []
        for agent in agents:
            matricule = agent[0]
            start_year = year - annee
            end_year = year
            cursor.execute(notes_query, (matricule, start_year, end_year))
            agent_notes = cursor.fetchall()
            notes.extend(agent_notes)
            somme_notes = sum(note[0] for note in notes)
            moyenne = somme_notes / len(notes) if len(notes) > 0 else 0
            moyenne_arrondie = round(moyenne, 2)
            cursor.execute("UPDATE resultat SET moyenne_note = ? WHERE matricule = ?", (moyenne_arrondie, agent[0]))
            conn.commit()

    conn.close()
    
def get_diplome():
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        sql = "SELECT libelle_diplome FROM diplome  "
        cursor.execute(sql)

        resultats = cursor.fetchall()

        cursor.close()
        conn.close()

        techniciens = [resultat[0] for resultat in resultats]
        return techniciens

    except Exception as e:
        print("Erreur lors de l'exécution de la requête SQL :", e)
        return []

def get_date_from_database(matricule):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT date_anc_grade FROM AGENT WHERE matricule = ?", (matricule,))
    date_anc_grade_tuple = cursor.fetchone()
    conn.close()

    if date_anc_grade_tuple:
        date_anc_grade = date_anc_grade_tuple[0]
        return date_anc_grade

def get_date_adm_from_database(matricule):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT date_anc_administration FROM AGENT WHERE matricule = ?", (matricule,))
    date_anc_adm = cursor.fetchone()
    conn.close()
    return date_anc_adm

#FONCTION ANCIENNETE ADMINISTRATION:
def anc_adm(matricule):
    # Obtenez la date de recrutement à partir de la base de données
    date_anc_adm_tuple = get_date_adm_from_database(matricule)
    # Vérifiez si la date de recrutement est disponible dans la base de données
    if date_anc_adm_tuple is None or date_anc_adm_tuple[0] is None:
        raise ValueError("La date de recrutement n'est pas disponible pour le matricule donné.")

    # Récupérer la chaîne de caractères de la date de recrutement
    date_anc_adm_str = date_anc_adm_tuple[0]  # Accéder à l'élément 0 du tuple

    # Convertir la chaîne de caractères en un objet datetime
    format_date = "%d/%m/%Y %H:%M"
    date_anc_adm = datetime.strptime(date_anc_adm_str, format_date)

    # Obtenir la date actuelle
    date_actuelle = datetime.now()

    # Calculer l'ancienneté en années complètes
    anciennete = date_actuelle.year - date_anc_adm.year

    # Vérifier si la date de recrutement est postérieure à la date actuelle
    if (date_anc_adm.month, date_anc_adm.day) > (date_actuelle.month, date_actuelle.day):
        anciennete -= 1

    # Calculer l'ancienneté administrative en attribuant 0.1 pour chaque année complète
    anciennete_administration = anciennete * 0.1
    return anciennete_administration
#calculer anc_adm pour tous les agents:
def calcule_toutes_anc_adm():
    with app.app_context():
        conn = get_db()
        cursor = conn.cursor()

        # Sélectionner les matricules des agents dont l'ordre est supérieur ou égal à 251 dans la table resultat
        cursor.execute("SELECT matricule FROM resultat LIMIT -1 OFFSET 800")
        matricules = cursor.fetchall()

        for matricule in matricules:
            matricule = matricule[0]  # Extraire le matricule du tuple
            anciennete_administration = anc_adm(matricule)  # Utiliser votre fonction anc_adm(matricule)

            # Mettre à jour le champ calcul_anc_administration dans la table resultat
            cursor.execute("UPDATE resultat SET calcul_anc_administration = ? WHERE matricule = ?", (anciennete_administration, matricule))

        conn.commit()
        conn.close()

# FONCTION ANCIENNETE GRADE :

def anc_grade(matricule):
    # Déclaration des constantes
    POINTS_PAR_AN = 2  # Nombre de points gagnés par année
    MAX_POINTS = 8     # Maximum de points possibles
    date_anc_grade = get_date_from_database(matricule)
    
    # Obtenir la date actuelle
    date_actuelle = datetime.now()
    
    # Calculer l'ancienneté en années
    date_format = "%d/%m/%Y %H:%M"
    try:
        date_anc_grade = datetime.strptime(date_anc_grade, date_format)
    except ValueError:
        raise ValueError("Le format de la date de fonction est incorrect.")
    anciennete = (date_actuelle - date_anc_grade).days / 365
    # Arrondir l'ancienneté à l'année la plus proche
    anciennete_arrondie = round(anciennete)

    # Calculer les points d'ancienneté en fonction du nombre d'années arrondies
    points_anciennete = anciennete_arrondie * POINTS_PAR_AN

    # Assurer que le total des points ne dépasse pas le maximum
    points = min(points_anciennete, MAX_POINTS)

    return points

def insert_liste_exc(grade):
    with app.app_context():
        conn = get_db()
        cursor = conn.cursor()
        sql = '''
        SELECT a.matricule, a.date_anc_grade
        FROM AGENT a
        INNER JOIN resultat r ON a.matricule = r.matricule
        INNER JOIN liste_exc le ON a.code_categorie = le.code_categorie AND a.code_corps = le.code_corps AND a.code_cadre = le.code_cadre AND a.code_grade = le.code_grade            
        INNER JOIN grades G ON G.code_categorie = le.code_categorie AND G.code_corps = le.code_corps AND G.code_cadre = le.code_cadre AND G.code_grade = le.code_grade 
        WHERE r.calcul_anc_grade >= 8
        AND le.libelle_grade = ?
        '''
        cursor.execute(sql, (grade,))
        agents = cursor.fetchall()
        for agent in agents:
            matricule, date_anc_grade = agent
            cursor.execute("SELECT COUNT(*) FROM AGENTS_EXCEPTION WHERE matricule = ?", (matricule,))
            count = cursor.fetchone()[0]

            if count == 0:
                # Mettre à jour le champ calcul_anc_administration dans la table resultat
                cursor.execute("INSERT INTO AGENTS_EXCEPTION (matricule, date_anc_grade) VALUES (?,?)",
                            (matricule, date_anc_grade))
            conn.commit()
        conn.close() 
        


#calculer anc_grade pour tous les agents:
def calcule_toutes_anc_grade():
    with app.app_context():
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT matricule FROM resultat where calcul_anc_grade >=8")
        matricules = cursor.fetchall()

        for matricule in matricules:
            matricule = matricule[0]  # Extraire le matricule du tuple
            anciennete_grade = anc_grade(matricule)  # Utiliser votre fonction anc_adm(matricule)

            # Mettre à jour le champ calcul_anc_administration dans la table session_agent
            cursor.execute("UPDATE resultat SET calcul_anc_grade = ? WHERE matricule = ?", (anciennete_grade, matricule))

        conn.commit()
        conn.close()
        
if __name__ == '__main__':
    app.run()
