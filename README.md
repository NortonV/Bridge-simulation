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

A terhelés egyenletesen oszlik meg a két végpontnál (W/2 - W/2), valamint **rögzített végi nyomatékok** is keletkeznek:
```
M_FEM = ± (w × L²) / 12
```
ahol **w** = W/L (egyenletesen megoszló terhelés N/m-ben).

Ez biztosítja, hogy hosszú gerendák is reálisan lehajlanak önsúlyuk hatására.

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

#### Maximális Hajlítási Nyomaték Meghatározása

A program pontosan számolja a hajlítási nyomatékot, figyelembe véve a terhelés helyzetét:

**1. Végponti nyomatékok** (slope-deflection módszerrel):
```
M_A = (2EI/L) × (2θ_A + θ_B - 3ψ) + M_FEM_A
M_B = (2EI/L) × (2θ_B + θ_A - 3ψ) + M_FEM_B
```

**2. Nyomaték a terhelési pontban** (ha Ixchel a gerendán áll):

Nyíróerő az A végpontnál:
```
V_A = P × b/L + (M_B - M_A)/L
```

Nyomaték a terhelési pontban (távolság 'a' az A ponttól):
```
M_load = M_A + V_A × a
```

**3. Maximális nyomaték kiválasztása**:
```
M_max = max(|M_A|, |M_B|, |M_load|)
```

Ez biztosítja, hogy a program felismerje a kritikus terhelést, még akkor is, ha az a gerenda közepén van (pl. egyszerű alátámasztású gerendák esetén).

#### Axiális Feszültség
```
σ_axial = N / A
```
Ahol **N** = axiális erő (± előjellel)

#### Hajlítási Feszültség
```
σ_bending = M_max × y / I
```
Ahol:
- **M_max** = maximális hajlítási nyomaték (lásd fent)
- **y** = távolság a semleges tengely től (= R/2 a szélső szálaknál)
- **I** = másodrendű nyomaték

#### Feszültségek Kombinálása

A gerenda keresztmetszetének különböző pontjain eltérő feszültségek ébrednek. A maximális feszültség a szélső szálaknál lép fel:

**Felső szál:**
```
σ_felső = σ_axial + σ_bending
```

**Alsó szál:**
```
σ_alsó = σ_axial - σ_bending
```

**Maximális feszültség:**
```
σ_max = max(|σ_felső|, |σ_alsó|)
```

**Példa:**
Egy gerenda nyomott (σ_axial = -100 MPa) és hajlított (σ_bending = +80 MPa):
- Felső szál: |-100 + 80| = |-20| = **20 MPa**
- Alsó szál: |-100 - 80| = |-180| = **180 MPa**
- Maximális feszültség: **180 MPa** (az alsó szál)

Így a program pontosan kiszámítja, hogy melyik szál éri el előbb a törési határt.

#### Terhelési Arány
```
stress_ratio = σ_max / σ_strength
```

Ha `stress_ratio ≥ 1.0` → **törés következik be**

### 7. Kihajlás Ellenőrzés (Euler-Buckling)

Nyomott gerendáknál (N < 0) kihajlási vizsgálat történik:

**Kritikus kihajlási erő**:
```
P_cr = (π² × E × I) / (K × L)²
```

Ahol:
- **K** = 1.0 (hatékony hossz tényező)
- **L** = gerenda hossza

**Megjegyzés a K-faktorról:**
- K=1.0: Csuklós-csuklós végek (amit a program feltételez)
- K=0.5: Befogott-befogott végek (4× erősebb, de bonyolult számítani)
- K=0.7: Befogott-csuklós végek

A program K=1.0 értéket használ, amely **biztonsági szempontból konzervatív** - kissé alulbecsüli a kihajlási teherbírást, de ez inkább előny, mint hátrány.

**Kihajlási arány**:
```
buckling_ratio = |N| / P_cr
```

**Végső terhelési arány**:
```
final_ratio = max(stress_ratio, buckling_ratio)
```

Ez biztosítja, hogy mind a szilárdsági, mind a stabilitási feltételek teljesüljenek.

### 8. Deformáció Megjelenítése

A deformált gerendák vizualizációja egyszerűsített görbékkel történik, amely figyelembe veszi:

- Végpontok elmozdulásait (u_x, u_y)
- Végpontok elforduásait (θ)
- A gerenda eredeti és deformált geometriáját

**Fontos:** A vizualizáció közelítő módszert használ a megjelenítéshez. A pontos fizikai számítások a végeselemes módszerrel történnek - a látott görbék csak szemléltetik az eredményeket.

---

## Fizikai Modell Pontossága és Korlátai

### ✓ Mit Tartalmaz a Szimuláció

1. **Pontos végeselemes analízis** (Finite Element Method)
   - Euler-Bernoulli gerenda elmélet
   - Axiális és hajlítási merevség
   - Hőtágulási hatások
   - Euler-féle kihajlás ellenőrzés

2. **Pontos terhelési modellek**
   - Gravitációs önsúly (csomóponti erők + rögzített végi nyomatékok)
   - Koncentrált pontterhelés (Ixchel karaktere)
   - Hőmérséklet változás hatása
   - Rögzített végi nyomatékok számítása

3. **Valós anyagtulajdonságok**
   - Rugalmassági modulusz (E)
   - Sűrűség és önsúly
   - Szakítószilárdság
   - Hőtágulási együttható

### ⚠️ Egyszerűsítések és Feltevések

1. **Lineáris rugalmas viselkedés**
   - A program kis deformációkat feltételez (geometriai linearitás)
   - Nem kezeli a képlékeny alakváltozást
   - Nagyon nagy deformációknál az eredmények pontatlanok lehetnek

2. **Statikus terhelés**
   - Nincs dinamikus hatás (rezgés, lökés)
   - Valós járás közben lökésszerű terhelések lennének

3. **2D síkbeli szerkezetek**
   - Csak egy síkban működik a szimuláció
   - Nincs csavaró nyomaték
   - Oldalirányú kihajlás nem modellezhető

4. **Kihajlási tényező (K = 1.0)**
   - A program csuklós-csuklós végeket feltételez
   - Valós kihajlási hossz függ a csomópontok merevségétől
   - Ez biztonságos közelítés, de alulbecsüli a teherbírást

### 📏 Mikor Megbízható a Szimuláció?

**Kiváló pontosság:**
- Rövid fesztávolságok (< 30 méter)
- Merev szerkezetek (kis elmozdulások)
- Normál hőmérséklet tartomány (-20°C - +50°C)

**Közepes pontosság:**
- Hosszú fesztávok (30-100 méter)
- Nagyobb deformációk (de még rugalmas tartomány)
- Extrém hőmérsékletek

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