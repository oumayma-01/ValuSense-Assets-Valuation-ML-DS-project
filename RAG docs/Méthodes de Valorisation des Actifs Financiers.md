# Méthodes de Valorisation des Actifs Financiers

## Vue d'ensemble

Les méthodes de valorisation des actifs financiers se répartissent en trois grandes approches :
1. **L'approche par le marché** (Market Approach)
2. **L'approche par les revenus** (Income Approach)  
3. **L'approche par le coût** (Cost Approach)

Le choix de la méthode dépend de la nature de l'actif, de la disponibilité des données et du contexte de l'évaluation.

---

## Tableau complet des méthodes de valorisation

| Catégorie (Approche) | Méthode / Technique | Principe de base | Formule / Mode de calcul | Quand l'utiliser ? | Lien avec Mark-to-Market / Model |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **A. APPROCHE PAR LE MARCHÉ** | **1. Mark-to-Market (MtM)** | Valorisation basée sur le **prix coté** sur un marché actif et liquide pour un actif **strictement identique**. | Prix = dernier cours de bourse, prix acheteur/vendeur (bid/ask) sur un marché réglementé, ou prix de référence d'un fournisseur de données. | Actifs très liquides : actions cotées, obligations d'État, devises majeures, contrats à terme standardisés. | **C'est le "Mark-to-Market" pur.** Méthode la plus fiable et objective, sans subjectivité. |
| | **2. Mark-to-Market par Comparables** | Valorisation basée sur les prix de transactions récentes d'actifs **similaires** (mais pas strictement identiques). | Ajustement du prix de la transaction comparable en fonction des différences de risque, maturité, taille, etc. | Actifs moins liquides : immobilier, participations privées, obligations corporate peu tradées. | **Mark-to-Market dégradé.** Données de marché (Niveau 2 IFRS) avec ajustements subjectifs. |
| | **3. Multiples de Marché** | Application d'un multiple (ratio) observé sur le marché à une variable financière de l'actif. | **Valeur = Multiple × Variable Financière** (ex: Valeur action = PER secteur × BPA de l'entreprise). | Valorisation d'entreprises non cotées par comparaison avec des sociétés cotées similaires. | **Mark-to-Market indirect.** Données de marché mais application subjective (choix des comparables, ajustements). |
| | **4. Matrix Pricing** | Estimation du prix d'une obligation basée sur une **courbe de rendement** pour des émetteurs de qualité comparable. | Interpolation du rendement sur la courbe des taux pour la maturité donnée, puis calcul du prix à partir de ce rendement. | Obligations non cotées, billets de trésorerie, papier commercial. | **Mark-to-Model** (utilisation d'un modèle de courbe des taux) **avec des données de marché observables** (taux, spreads). |
| **B. APPROCHE PAR LES REVENUS** | **5. Actualisation des Flux de Trésorerie (DCF)** | La valeur est la **somme des flux de trésorerie futurs** attendus, actualisés à un taux reflétant leur risque. | **Valeur = Σ (FCFₜ / (1 + WACC)ᵗ) + (Valeur Terminale / (1 + WACC)ⁿ)** où WACC = Coût moyen pondéré du capital. | Actifs générateurs de revenus prévisibles : entreprises, projets d'investissement, immobilier locatif. | **Pur "Mark-to-Model"** : toute la valeur repose sur des hypothèses internes (croissance, taux, marges). |
| | **6. Modèle d'Actualisation des Dividendes (DDM)** | Cas particulier du DCF. La valeur d'une action est la somme des **dividendes futurs** actualisés. | **Modèle de Gordon : Valeur = D₁ / (r - g)** où D₁ = dividende futur, r = taux exigé, g = taux de croissance. | Valorisation d'actions de sociétés matures versant des dividendes réguliers et stables. | **Mark-to-Model** : repose entièrement sur des prévisions internes de dividendes et de croissance. |
| **C. APPROCHE PAR LE COÛT** | **7. Coût de Remplacement** | La valeur est égale au **coût de reproduction** ou de remplacement de l'actif, diminué de l'usure et de l'obsolescence. | **Valeur = Coût de remplacement neuf - Dépréciation (physique, fonctionnelle, économique)**. | Actifs corporels spécifiques (machines, usines, brevets), ou filiales sans marché ni flux prévisionnels. | **Mark-to-Model** : les coûts de construction et les durées de vie sont des estimations internes. |
| | **8. Coût de Reproduction** | Calcul du coût pour reproduire exactement l'actif à l'identique. | Somme des coûts directs et indirects pour reconstruire l'actif. | Actifs uniques ou historiques, ou en assurance pour estimer la valeur à neuf. | **Mark-to-Model** pur. |
| **D. MÉTHODES HYBRIDES** | **9. Option Réelles** | Valorisation de la **flexibilité managériale** (option de retarder, étendre, abandonner un projet) via des modèles mathématiques. | **Valeur = VAN classique + Valeur des options managériales.** Modèles Black-Scholes ou binomial. | Projets très incertains (R&D, ressources naturelles, start-ups) avec décisions stratégiques. | **Mark-to-Model avancé** : repose sur des modèles stochastiques et des hypothèses de volatilité internes. |
| | **10. Valeur de Liquidation** | Estimation de la valeur obtenue si l'actif ou l'entreprise était **vendu en morceaux**. | Somme des valeurs de marché estimées pour chaque actif moins les passifs. | Entreprises en difficulté, faillite, ou pour établir un "prix plancher". | Peut être **Mark-to-Market** (prix de revente) ou **Mark-to-Model** (coûts de cession estimés). |

---

## Hiérarchie des données (Normes IFRS 13)

| Niveau | Description | Exemples | Méthodes associées |
| :--- | :--- | :--- | :--- |
| **Niveau 1** | Données les plus fiables : prix cotés sur un marché actif pour un actif identique. | Actions cotées en bourse, obligations d'État. | Mark-to-Market pur |
| **Niveau 2** | Données observables mais non cotées directement : prix d'actifs similaires, taux d'intérêt, courbes de rendement. | Matrix Pricing, obligations corporate peu tradées. | Mark-to-Market dégradé / Mark-to-Model avec données observables |
| **Niveau 3** | Données non observables : hypothèses et modèles internes de l'évaluateur. | DCF, DDM, Options Réelles. | Mark-to-Model pur |

---

## Mark-to-Market vs Mark-to-Model

| Critère | **Mark-to-Market (MtM)** | **Mark-to-Model (MtM - modèle)** |
| :--- | :--- | :--- |
| **Source de la valeur** | **Prix de marché observables** et objectifs (Niveau 1 et 2). | **Modèles mathématiques** et hypothèses internes (Niveau 3). |
| **Objectivité** | Très élevée (peu de place à l'interprétation). | Faible (forte subjectivité des paramètres d'entrée). |
| **Exemples** | Actions cotées, obligations d'État, devises. | DCF, DDM, Option Réelles, Matrix Pricing. |
| **Avantage** | Fiable, transparent, facile à auditer. | Permet de valoriser des actifs sans marché. |
| **Inconvénient** | Ne fonctionne que pour les actifs liquides. | Peut être manipulé ("faire dire au modèle ce qu'on veut"), surtout en période de stress. |
| **Utilisation en IFRS** | Correspond aux données de Niveau 1. | Correspond aux données de Niveau 3 (et parfois Niveau 2). |

---

## En pratique

Les professionnels utilisent souvent un **mix des approches** :
- Ils commencent par un **mark-to-market** si les données sont disponibles.
- Si les données manquent, ils complètent avec un **mark-to-model**.
- Toutes les hypothèses doivent être **documentées** pour respecter les normes IFRS 13 sur la **juste valeur** (*fair value*).

---

## Références normatives

- **IFRS 13** : Définit la juste valeur et établit la hiérarchie des données.
- **IAS 36** : Traite des dépréciations d'actifs.
- **IAS 39 / IFRS 9** : Concernent les instruments financiers et leur évaluation.