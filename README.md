# Ixchel Hídja

## Áttekintés

Az **Ixchel Hídja** egy fizikai szimuláción alapuló hídépítő program, amely lehetővé teszi mérnöki szerkezetek tervezését, analízisét és tesztelését valós idejű vizualizációval. A program 2D keretszerkezeteket szimulál pontos statikai analízissel, figyelembe véve az anyagi tulajdonságokat, hőmérsékleti hatásokat és kihajlási jelenségeket.

---

## Főbb Jellemzők

### 1. Építési Mód (Build Mode)

#### Alapvető Funkciók
- **Csomópontok elhelyezése**: Kattintással új csomópontokat lehet létrehozni
- **Gerendák rajzolása**: Két csomópont között húzással gerendát lehet rajzolni
- **Fix támaszok**: A 2 piros csomópont rögzített támasz, nem tud elmozdulni
- **Intelligens csatlakozás**: A gerendák automatikusan feldarabolódnak kereszteződési pontoknál
- **4 anyagtípus**:
  - **Fa** (1)
  - **Bambusz** (2)
  - **Acél** (3)
  - **Spagetti** (4)

#### Speciális Eszközök

**Ív Eszköz (A billentyű)**
- *1. fázis*: Húzd ki az ív alapját (kezdő és végpont megadása)
- *2. fázis*: Mozgasd az egeret az ív magasságának beállításához
- Bal klikk: Véglegesítés - az ív 8 gerendaszegmensből épül fel automatikusan
- Jobb klikk: Mégse

**Törlés Eszköz (X billentyű)**
- Tartsd lenyomva a bal egérgombot a csomópontok és gerendák eltávolításához
- A rögzített támaszokat nem lehet törölni

**Csomópontok Mozgatása**
- Jobb klikk + húzás: Csomópont áthelyezése
- Elengedéskor automatikus összeolvadás közeli csomópontokkal
- Vagy automatikus illesztés közeli gerendákra

### 2. Szimulációs Mód

A **SPACE** billentyű megnyomásával indítható el az analízis mód, ahol:

#### Ixchel Karakter Vezérlése
- **Bal/Jobb nyíl**: Mozgás a hídon
- **R billentyű**: Karakter felemeles (újrapozicionálás)
- A karakter súlya és sebessége a tulajdonságok menüben állítható

#### Vizuális Megjelenítés
A program háromféle nézet közül lehet választani (**V** billentyű):

1. **Erők nézet**: 
   - Kék színnel jelzi a nyomást
   - Piros színnel jelzi a húzást

2. **Anyagminta nézet**:
   - Minden gerenda eredeti anyagszínében látszik

3. **Terhelés nézet**:
   - Színátmenet az anyagszíntől a pirosig
   - A piros szín a töréshez közeli állapotot jelzi

#### Feliratok (**T** billentyű)
- **Pontos értékek**: Axiális erő és hajlítási nyomaték Newton-ban (pl. "1250N | 450N")
- **Százalékos terhelés**: A gerenda törési határához viszonyított terhelés
- **Nincs**: Feliratok elrejtése

#### Torzítás Szabályzó
- A **G** billentyűvel megnyitható grafikonon található csúszka
- Logaritmikus skála: 1× - 1000×
- Alapértelmezett: 100×
- Nagyítja a deformációkat a jobb láthatóság érdekében
- **Fontos**: A fizikai számítások mindig pontos értékekkel dolgoznak (1× torzítás)

### 3. Tulajdonságok Menü (M vagy ESC billentyű)

#### Anyagtulajdonságok (anyagonként külön beállítható)

**Rugalmassági modulus (E)**
- A merevséget határozza meg
- Mértékegység: GPa
- Nagyobb érték → kevesebb deformáció

**Sűrűség**
- Az anyag tömege térfogategységenként
- Mértékegység: kg/m³
- Befolyásolja a szerkezet önsúlyát

**Szakítószilárdság**
- A maximálisan elviselhető feszültség
- Mértékegység: MPa (megapascal)
- A gerenda ennél nagyobb feszültségnél törik


**Gerenda vastagság**
- A keresztmetszet átmérője
- Mértékegység: méter
- Befolyásolja a súlyt és a teherbírást

**Üregesség arány**
- A gerenda belső üreg mérete (0% = tömör, 99% = majdnem üres cső)
- Könnyebbé teszi a gerendát, de csökkenti a teherbírást
- Üreges gerendával ugyanakkora sulyú részlet nagyobb átmérőjű -> később éri el a kritikus kihajlási erőt (Euler-buckling)

#### Globális Beállítások

**Alap hőmérséklet**
- Az az építéskori hőmérséklet
- Mértékegység: °C
- Ez a referencia hőmérséklet

**Szimulációs hőmérséklet**
- A hőmérséklet szimulációkor
- A különbség hőtágulási feszültségeket hoz létre

#### Ixchel Tulajdonságok

**Tömeg**
- Ixchel karakter súlya
- Mértékegység: kg
- Logaritmikus skála: 0.1 - 1500 kg

**Sebesség**
- Mozgás gyorsasága
- Mértékegység: m/s
- Lineáris skála: 1 - 20 m/s

---

## Billentyűparancsok Összefoglalása

### Általános Vezérlés
- **SPACE**: Szimuláció indítása/leállítása
- **M / ESC**: Tulajdonságok menü megnyitása/bezárása
- **G**: Grafikon megjelenítése/elrejtése

- **↑ / ↓** vagy **Egér Görgő**: Hangerő szabályzása

### Építési Mód
- **1-4**: Anyagtípus kiválasztása (Fa/Bambusz/Acél/Spagetti)
- **X**: Törlés eszköz
- **A**: Ív eszköz be/ki
- **Ctrl+S**: Híd mentés
- **Ctrl+L**: Híd betöltés

### Szimulációs Mód
- **Bal/Jobb nyíl**: Ixchel mozgatása
- **V**: Nézet váltása (Erők/Anyag/Terhelés)
- **T**: Feliratok váltása (Értékek/Százalék/Nincs)

---

## Fizikai Számítások

### 1. Alkalmazott Módszer: Végeselemes Statikai Analízis (Finite Element Method)

A program a **keretszerkezetek** statikai analízisére optimalizált végeselemes módszert használ. Ez a módszer:

#### Alapelv
A szerkezetet diszkrét elemekre (gerendákra) és csomópontokra bontja, majd az egyensúlyi egyenleteket mátrix formában oldja meg:

```
K × U = F
```

Ahol:
- **K** = globális merevségi mátrix (stiffness matrix)
- **U** = elmozdulás vektor (csomópontok elmozduláasai és elforduásai)
- **F** = terhelési vektor (erők és nyomatékok)

#### Szabadságfokok (Degrees of Freedom - DOF)
Minden csomópont 3 szabadsági fokkal rendelkezik:
- **u_x**: Vízszintes elmozdulás
- **u_y**: Függőleges elmozdulás
- **θ**: Elforduás (szögelfordulás)

### 2. Lokális Merevségi Mátrix

Minden gerenda elemnél egy 6×6-os lokális merevségi mátrix épül fel, amely tartalmazza:

**Axiális merevség** (nyújtás/összenyomás):
```
EA/L
```

**Hajlítási merevség** (bending):
```
12EI/L³   (keresztirányú erő)
4EI/L     (hajlítási nyomaték)
```

Ahol:
- **E** = rugalmassági modulus
- **A** = keresztmetszeti terület
- **I** = másodrendű nyomaték (inercia)
- **L** = gerenda hossza

#### Keresztmetszeti Paraméterek (Körkeresztmetszet)

**Terület (A)**:
```
A = π(R² - r²)
```

**Másodrendű nyomaték (I)**:
```
I = (π/4)(R⁴ - r⁴)
```

Ahol:
- **R** = külső sugár (= vastagság/2)
- **r** = belső sugár (= R × üregesség_arány)

### 3. Koordináta Transzformáció

Mivel a gerendák különböző szögekben helyezkednek el, a lokális mátrixot át kell transzformálni globális koordinátarendszerbe:

```
K_global = T^T × K_local × T
```

A transzformációs mátrix (T) tartalmazza a gerenda irányítását:
- **c** = cos(α) - vízszintes irány koszinusza
- **s** = sin(α) - függőleges irány szinusza
- **α** = gerenda dőlésszöge

### 4. Terhelések

#### a) Önsúly (Gravitációs Teher)
Minden gerendára hat az önsúlya:
```
W = ρ × A × L × g
```
Ahol:
- **ρ** = sűrűség
- **g** = 9.81 m/s² (nehézségi gyorsulás)

A terhelés egyenletesen oszlik meg a két végpontnál (W/2 - W/2).

#### b) Pontszerű Teher (Ixchel)
A karakternek a gerendán való elhelyezkedése **ekvivalens csomóponti terhelésekre** bomlik:

**Reakcióerők**:
```
R_A = P × b²(3a + b) / L³
R_B = P × a²(a + 3b) / L³
```

**Rögzített végi nyomatékok** (Fixed-End Moments):
```
M_A = -P × a × b² / L²
M_B = +P × a² × b / L²
```

Ahol:
- **P** = Ixchel tömege × g
- **a** = távolság A csomóponttól
- **b** = L - a (távolság B csomóponttól)
- **L** = gerenda hossza

#### c) Hőterhelés
Hőmérsékletváltozás feszültségeket okoz:
```
σ_thermal = E × α × ΔT
F_thermal = -E × A × α × ΔT
```

Ahol:
- **ΔT** = T_szimuláció - T_alap
- **α** = hőtágulási együttható

### 5. Slope-Deflection Módszer

A végpontok nyomatékának számítása az elmozdulásokból:

```
M_AB = (2EI/L) × (2θ_A + θ_B - 3ψ) + M_FEM
```

Ahol:
- **θ_A, θ_B** = végpontok elforduásai
- **ψ** = (v_B - v_A) / L = vízszintes elmozdulás / hossz
- **M_FEM** = rögzített végi nyomaték (terheléstől függő)

### 6. Feszültségszámítás

#### Axiális Feszültség
```
σ_axial = N / A
```
Ahol **N** = axiális erő (± előjellel)

#### Hajlítási Feszültség
```
σ_bending = M × y / I
```
Ahol:
- **M** = hajlítási nyomaték
- **y** = távolság a semleges tengely től (= R/2 a szélső szálaknál)
- **I** = másodrendű nyomaték

#### Összes Feszültség
```
σ_total = |σ_axial| + |σ_bending|
```

#### Terhelési Arány
```
stress_ratio = σ_total / σ_strength
```

Ha `stress_ratio ≥ 1.0` → **törés következik be**

### 7. Kihajlás Ellenőrzés (Euler-Buckling)

Nyomott gerendáknál (N < 0) kihajlási vizsgálat történik:

**Kritikus kihajlási erő**:
```
P_cr = (π² × E × I) / (K × L)²
```

Ahol:
- **K** = 1.0 (hatékony hossz tényező, egyszerű alátámasztásra)
- **L** = gerenda hossza

**Kihajlási arány**:
```
buckling_ratio = |N| / P_cr
```

**Végső terhelési arány**:
```
final_ratio = max(stress_ratio, buckling_ratio)
```

Ez biztosítja, hogy mind a szilárdsági, mind a stabilitási feltételek teljesüljenek.

### 8. Deformáció Megjelenítése (Hermite Spline)

A deformált gerendák vizualizációja **kubikus Hermite-spline** görbékkel történik, amely figyelembe veszi:

- Végpontok elmozdulásait (u_x, u_y)
- Végpontok elforduásait (θ)
- A gerenda eredeti és deformált geometriáját

A spline paraméterezése:
```
v = L × (h1 × rot1 + h2 × rot2)
u = t × L
```

Ahol:
- **h1, h2** = Hermite-bázisfüggvények
- **rot1, rot2** = relatív elforduások a deformált húrhoz képest
- **t** = paraméter (0...1)
- **v** = merőleges eltérés
- **u** = hosszirányú távolság

---

## A Módszer Előnyei és Korlátai

### Előnyök ✓

1. **Pontos statikai analízis**: A lineáris rugalmas tartománybancalculates pontos eredményeket ad
2. **Hatékony számítás**: Nagy szerkezeteknél is gyors
3. **Tetszőleges geometria**: Bármilyen 2D keretszerkezet modellezhető
4. **Többféle terhelés**: Gravitáció, ponszerű teher, hőmérséklet egyidejűleg
6. **Valós idejű**: Minden keretváltásnál újraszámol, ezért interaktív

### Korlátok ⚠

1. **Rugalmas tartomány**: A képlékeny alakváltozást nem szimulálja
2. **Statikus**: Dinamikus hatásokat (rezgés, lökés) nem vesz figyelembe
3. **2D**: Csak síkbeli szerkezetekre működik
4. **Nyomaték csak végpontokon**: A gerenda közepén lévő maximális nyomatékot nem számolja pontosan
5. **Nincs szimulált törés**: Ha a híd eltörik, megáll a szimuláció

---

## Telepítés és Futtatás

### Követelmények
- Python 3.8 vagy újabb
- Pygame könyvtár
- NumPy könyvtár

### Telepítés
- A start.bat futtatása a pythont és minden szükséges könyvtárat letölt, majd elindítja a programot.

### Futtatás
- A start.bat fájl vagy a main.py fájl futtatásával.

A program teljes képernyős módban indul. **Kilépés**: Tulajdonságok menü → Kilépés gomb (vagy alt+f4).