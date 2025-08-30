🚀 Polyglot Bench - Benchmark Multi-Langages 

⏱️ Suite de tests comparant les performances de Python, Rust, Go et TypeScript sur 18 tests algorithmiques. Métriques d'exécution, mémoire et extensibilité.

---

📖 Sommaire

1. Objectifs
2. Langages Comparés
3. Métriques Mesurées
4. Installation et Utilisation
5. Résultats et Visualisation
6. Contributions
7. License
8. Contact

---

🎯 Objectifs

Ce projet vise à comparer objectivement les performances de Python, Rust, Go et TypeScript via 18 tests algorithmiques (tris, calculs mathématiques, traitements de données, etc.). Les résultats aident à choisir le langage adapté à des cas d'usage spécifiques (calcul intensif, concurrence, etc.) .

---

🔧 Langages Comparés

Langage Version Use Case Principal
Python 3.10+ Scripting, AI
Rust 1.60+ Système, Performances
Go 1.18+ Concurrence, CLI
TypeScript 4.9+ Web, Fullstack

---

📊 Métriques Mesurées

· ⏱️ Temps d'exécution (moyenne, médiane, écart-type).
· 💾 Utilisation mémoire (pic de mémoire, allocation heap).
· 🔥 Charge CPU (via des outils comme perf ou py-spy).

---

🛠️ Installation et Utilisation

Prérequis

· Installer les langages : Python, Rust, Go, Node.js (TypeScript).
· Cloner le repo :
  ```bash
  git clone https://github.com/votre-username/polyglot-bench.git
  cd polyglot-bench
  ```

Exécution des Tests

1. Lancer tous les tests :
   ```bash
   ./run_benchmarks.sh  # Script unifié pour tous les langages
   ```
2. Exécuter un langage spécifique :
   ```bash
   cd python && python run_tests.py
   cd ../rust && cargo run --release
   ```

---

📈 Résultats et Visualisation

Les résultats sont exportés en JSON et visualisables via :

· Un dashboard HTML généré avec Chart.js .
· Des graphiques comparatifs (temps vs. mémoire).
· Exemple de visualisation :
  ```bash
  python visualize_results.py  # Génère des graphs dans `results/`
  ```

---

🤝 Contributions

Les contributions sont bienvenues ! Pour ajouter un test ou un langage :

1. Forkez le projet.
2. Créez un dossier pour le nouveau langage (ex. java).
3. Implémentez les 18 tests dans le langage.
4. Ajoutez les métriques de performance dans metrics.json.
5. Soumettez une pull request .

---

📜 License

Ce projet est sous license MIT. Voir le fichier LICENSE pour plus de détails.

---

📞 Contact

· Auteur : Votre Nom
· Email : votre.email@domain.com
· LinkedIn : Votre Profil

---

🎨 Badges et Statistiques

Ajoutez des badges pour rendre le README plus visuel  : https://img.shields.io/badge/License-MIT-blue.svg https://img.shields.io/github/issues/votre-username/polyglot-bench https://img.shields.io/github/stars/votre-username/polyglot-bench

---

💡 Conseils Supplémentaires

· Utilisez des graphiques interactifs (Chart.js/D3) pour les résultats.
· Ajoutez une section FAQ pour répondre aux questions courantes.
· Intégrez des exemples de code pour montrer un test typique .

Exemple de code en Python (test de Fibonacci) :

```python
def fibonacci(n: int) -> int:
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
```

Exemple de code en Rust (test de tri) :

```rust
pub fn quick_sort<T: Ord>(arr: &mut [T]) {
    if arr.len() <= 1 {
        return;
    }
    let pivot = partition(arr);
    quick_sort(&mut arr[0..pivot]);
    quick_sort(&mut arr[pivot+1..]);
}
```
