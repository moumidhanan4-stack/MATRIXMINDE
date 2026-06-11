from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import time

app = Flask(__name__)
CORS(app)

# ---------------------------------------------------------
# 1. Méthode de GAUSS (Directe)
# ---------------------------------------------------------
def solve_gauss(A, b):
    n = len(A)
    Ab = np.hstack([A, b.reshape(-1, 1)])
    steps = []
    
    for i in range(n):
        steps.append({"label": f"Pivot L{i+1}", "matrix": Ab.copy().tolist()})
        # Partial Pivoting
        max_row = np.argmax(abs(Ab[i:n, i])) + i
        Ab[[i, max_row]] = Ab[[max_row, i]]
        
        for k in range(i + 1, n):
            factor = Ab[k, i] / Ab[i, i]
            Ab[k, i:] -= factor * Ab[i, i:]
            
    x = np.zeros(n)
    for i in range(n - 1, -1, -1):
        x[i] = (Ab[i, n] - np.dot(Ab[i, i+1:n], x[i+1:n])) / Ab[i, i]
    
    return x.tolist(), steps

# ---------------------------------------------------------
# 2. Décomposition LU (Directe)
# ---------------------------------------------------------
def solve_lu(A, b):
    n = len(A)
    L = np.eye(n)
    U = A.copy()
    
    for i in range(n):
        for k in range(i + 1, n):
            factor = U[k, i] / U[i, i]
            L[k, i] = factor
            U[k, i:] -= factor * U[i, i:]
    
    y = np.linalg.solve(L, b)
    x = np.linalg.solve(U, y)
    
    steps = [
        {"label": "Matrice L", "matrix": L.tolist()},
        {"label": "Matrice U", "matrix": U.tolist()}
    ]
    return x.tolist(), steps

# ---------------------------------------------------------
# 3. JACOBI (Itérative) - MODIFIÉ POUR RETOURNER LES STEPS
# ---------------------------------------------------------
def solve_jacobi(A, b, x0, tol, max_iter):
    A = np.array(A, dtype=float)
    b = np.array(b, dtype=float)
    n = len(A)
    x = np.array(x0, dtype=float)
    errors = []
    steps = [] 
    
    # Faktor dyal l-fren (Relaxation) bach n-awslo l-0.5
    omega = 0.5 

    D = np.diag(np.diag(A))
    LU = A - D
    
    for i in range(max_iter):
        # 1. Calcul dyal x_new raw (dakchi li knti kadi-ri)
        x_raw = np.linalg.solve(D, b - np.dot(LU, x))
        
        # 2. L-UPDATE S-7I7 (Relaxation)
        # Hna kankhlliw x takhd n-nass m-l-9dim o n-nass m-l-jdid
        x_new = (1 - omega) * x + omega * x_raw
        
        err = np.linalg.norm(x_new - x, ord=np.inf)
        
        errors.append(float(err))
        steps.append({"label": f"Iter {i+1}", "matrix": [x_new.tolist()]})
        
        # Updati x b-l-valeur li fiha l-fren
        x = x_new
        
        if err < tol: 
            break
            
        if i > 50 and len(errors) > 1 and err >= errors[-2]:
            break
            
    return x.tolist(), i + 1, errors, steps
# ---------------------------------------------------------
# 4. GAUSS-SEIDEL (Itérative) - MODIFIÉ POUR RETOURNER LES STEPS
# ---------------------------------------------------------
def solve_gauss_seidel(A, b, x0, tol, max_iter):
    n = len(A)
    x = np.array(x0, dtype=float)
    errors = []
    steps = []
    for it in range(max_iter):
        x_old = x.copy()
        for i in range(n):
            sum_j = np.dot(A[i, :i], x[:i]) + np.dot(A[i, i+1:], x_old[i+1:])
            x[i] = (b[i] - sum_j) / A[i, i]
        err = np.linalg.norm(x - x_old, ord=np.inf)
        errors.append(float(err))
        
        # إضافة حل كل دورة للمراحل
        steps.append({"label": f"Iter {it+1}", "matrix": [x.tolist()]})
        
        if err < tol: break
    return x.tolist(), it + 1, errors, steps

# ---------------------------------------------------------
# 5. GRADIENT CONJUGUÉ (Itérative) - MODIFIÉ POUR RETOURNER LES STEPS
# ---------------------------------------------------------
def solve_gradient_conjugue(A, b, x0, tol, max_iter):
    x = np.array(x0, dtype=float)
    r = b - np.dot(A, x)
    p = r.copy()
    errors = []
    steps = []
    
    for i in range(max_iter):
        Ap = np.dot(A, p)
        
        # 1. Calcul dyal alpha
        pAp = np.dot(p, Ap)
        if abs(pAp) < 1e-20: break
        
        alpha = np.dot(r, r) / pAp
        
        # 2. X_new o R_new
        x_new = x + alpha * p
        r_new = r - alpha * Ap
        
        # 3. Calcul dyal l-erreur
        err = np.linalg.norm(r_new, ord=2)
        
        # 4. Enregistrement dyal l-data (bach ybano l-graphe o l-détails)
        errors.append(float(err))
        steps.append({"label": f"Iter {i+1}", "matrix": [x_new.tolist()]})
        
        # --- L-BLASA L-MOUHIMA ---
        # Khbbiw r.r l-9dima l-beta 9bel mat-updata x o r
        old_r_dot_r = np.dot(r, r)
        
        # Updatiw x o r nichan hna
        x = x_new
        r = r_new
        # -------------------------

        if err < tol: 
            break
        
        beta = np.dot(r, r) / old_r_dot_r
        p = r + beta * p
        
    return x.tolist(), i + 1, errors, steps

# ---------------------------------------------------------
# API ROUTE
# ---------------------------------------------------------
@app.route('/solve', methods=['POST'])
def solve():
    try:
        data = request.json
        A = np.array(data['A'], dtype=float)
        B = np.array(data['B'], dtype=float)
        method = data['method']
        x0 = np.array(data.get('x0', [0]*len(B)), dtype=float)
        eps = float(data.get('epsilon', 0.001))
        max_it = int(data.get('maxIter', 100))
        
        start_time = time.time()
        steps, errors = [], [0]
        iters = 1
        
        if method == 'gauss':
            sol, steps = solve_gauss(A, B)
            errors = [1, 0.1, 0.0001] # Dummy pour l'affichage
        elif method == 'lu':
            sol, steps = solve_lu(A, B)
        elif method == 'jacobi':
            sol, iters, errors, steps = solve_jacobi(A, B, x0, eps, max_it)
        elif method == 'gauss_seidel':
            sol, iters, errors, steps = solve_gauss_seidel(A, B, x0, eps, max_it)
        elif method == 'gradient':
            sol, iters, errors, steps = solve_gradient_conjugue(A, B, x0, eps, max_it)
        else:
            return jsonify({"status": "error", "message": "Méthode inconnue"})

        execution_time = round((time.time() - start_time) * 1000, 3)
        
        return jsonify({
            "status": "success",
            "data": {
                "solution": sol,
                "iterations": iters,
                "time": execution_time,
                "steps": steps,
                "errors": errors
            }
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    # Zid use_reloader=False
    app.run(debug=True, port=5000, use_reloader=False)

    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            response = jsonify({})
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add("Access-Control-Allow-Headers", "*")
            response.headers.add("Access-Control-Allow-Methods", "*")
        return response