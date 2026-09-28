"""Reviewed UI translations. French source strings are stable message identifiers."""

MESSAGES = r"""
Plateforme de traitement des données|||DataFlow Studio|||منصّة معالجة وتحويل البيانات
VOTRE ESPACE DE PRÉPARATION|||YOUR DATA WORKSPACE|||مساحة إعداد بياناتك
Parcours|||Workflow|||سير العمل
Vue d’ensemble|||Overview|||نظرة عامة
1 · Importer|||1 · Import|||1 · الاستيراد
2 · Préparer|||2 · Prepare|||2 · الإعداد
3 · Contrôler|||3 · Review|||3 · المراجعة
4 · Exporter|||4 · Export|||4 · التصدير
Journal|||Run history|||سجل العمليات
Traitement des données|||Data processing|||معالجة البيانات
Les fichiers sont traités sur le serveur de l’application. Téléchargez vos résultats et vos recettes pour les conserver.|||Files are processed on the application server. Download your results and recipes to keep them.|||تُعالَج الملفات على خادم التطبيق. نزّل نتائجك ووصفات المعالجة للاحتفاظ بها.
Version 0.2 · Édition de démonstration|||Version 0.2 · Demo edition|||الإصدار 0.2 · نسخة تجريبية
Vider la session|||Clear session|||مسح الجلسة
:material/science: Mode démonstration · données fictives, aucune donnée client|||:material/science: Demo mode · synthetic data, no client data|||:material/science: وضع العرض التجريبي · بيانات افتراضية، دون بيانات عملاء
DE LA SOURCE À L’ANALYSE|||FROM SOURCE TO ANALYSIS|||من المصدر إلى التحليل
Des données prêtes.\nDes traitements reproductibles.|||Ready-to-use data.\nRepeatable workflows.|||بيانات جاهزة للاستخدام.\nمعالجة قابلة للتكرار.
Rassemblez vos fichiers, définissez vos règles et préparez des données traçables pour vos analyses.|||Bring your files together, define your rules and prepare traceable data for analysis.|||اجمع ملفاتك وحدد قواعدك وأعدّ بيانات قابلة للتتبع لتحليلاتك.
Importer mes fichiers|||Import my files|||استيراد ملفاتي
Explorer la démonstration|||Explore the demo|||استكشاف العرض التجريبي
01  Rassembler|||01  Collect|||01  جمع البيانات
02  Standardiser|||02  Standardize|||02  توحيد البيانات
03  Livrer|||03  Deliver|||03  تسليم النتائج
CSV, Excel, JSON, Parquet et tables PDF dans un seul espace.|||CSV, Excel, JSON, Parquet and PDF tables in one workspace.|||ملفات CSV وExcel وJSON وParquet وجداول PDF في مساحة واحدة.
Des règles explicites et des recettes que vous pouvez réutiliser.|||Explicit rules and recipes you can reuse.|||قواعد واضحة ووصفات معالجة قابلة لإعادة الاستخدام.
Des données validées, une quarantaine et un rapport de traçabilité.|||Validated data, quarantined rows and a traceability report.|||بيانات متحقق منها وصفوف معزولة وتقرير تتبع.
Une recette, plusieurs traitements|||One recipe, many runs|||وصفة واحدة لعمليات متعددة
Prévisualisez les sources, choisissez les types de colonnes et contrôlez les valeurs obligatoires. Enregistrez ensuite votre recette JSON pour préparer les prochains fichiers de même structure.|||Preview sources, choose column types and check required values. Then save your JSON recipe to prepare future files with the same structure.|||عاين المصادر واختر أنواع الأعمدة وتحقق من القيم المطلوبة. ثم احفظ وصفة JSON لإعداد الملفات القادمة ذات البنية نفسها.
Import → Préparation → Contrôle → Export|||Import → Prepare → Review → Export|||استيراد ← إعداد ← مراجعة ← تصدير
À savoir avant de commencer|||Before you start|||قبل البدء
25 Mo par fichier · 20 fichiers par lot · 100 000 lignes par traitement.|||25 MB per file · 20 files per batch · 100,000 rows per run.|||25 ميغابايت لكل ملف · 20 ملفًا لكل دفعة · 100,000 صف لكل عملية.
PDF : tables textuelles avec vérification obligatoire. OCR et surveillance automatique de dossier non inclus.|||PDF: text-based tables with mandatory review. OCR and automatic folder monitoring are not included.|||PDF: جداول نصية تتطلب المراجعة. التعرف الضوئي على الحروف ومراقبة المجلدات تلقائيًا غير متاحين.
Importez vos fichiers ou ouvrez la démonstration pour commencer.|||Import your files or open the demo to get started.|||استورد ملفاتك أو افتح العرض التجريبي للبدء.
Importer des fichiers|||Import files|||استيراد الملفات
ÉTAPE 01 / 04|||STEP 01 / 04|||الخطوة 01 / 04
ÉTAPE 02 / 04|||STEP 02 / 04|||الخطوة 02 / 04
ÉTAPE 03 / 04|||STEP 03 / 04|||الخطوة 03 / 04
ÉTAPE 04 / 04|||STEP 04 / 04|||الخطوة 04 / 04
Rassemblez vos sources|||Bring your sources together|||اجمع مصادر بياناتك
Importez plusieurs fichiers. Vous pourrez sélectionner les feuilles ou tables à préparer.|||Import multiple files, then select the sheets or tables to prepare.|||استورد عدة ملفات، ثم اختر الأوراق أو الجداول المراد إعدادها.
Déposez vos fichiers|||Upload your files|||ارفع ملفاتك
Paramètres de lecture|||Import settings|||إعدادات القراءة
Ces paramètres s’appliquent au lot importé. UTF-8 et détection du séparateur par défaut.|||These settings apply to the imported batch. Defaults: UTF-8 and automatic delimiter detection.|||تُطبق هذه الإعدادات على الدفعة المستوردة. الإعداد الافتراضي: UTF-8 واكتشاف الفاصل تلقائيًا.
Encodage texte|||Text encoding|||ترميز النص
Séparateur CSV / TXT|||CSV / TXT delimiter|||فاصل CSV / TXT
Détecter|||Auto-detect|||اكتشاف تلقائي
Tabulation|||Tab|||جدولة
Ligne d’en-tête Excel|||Excel header row|||صف العناوين في Excel
Chemin JSON vers la liste d’objets|||JSON path to the list of objects|||مسار JSON إلى قائمة الكائنات
Exemple : data.records|||Example: data.records|||مثال: data.records
Analyser les fichiers|||Analyze files|||تحليل الملفات
Limite du lot : 20 fichiers et 100 Mo au total.|||Batch limit: 20 files and 100 MB in total.|||حد الدفعة: 20 ملفًا و100 ميغابايت إجمالًا.
Lecture du lot…|||Reading the batch…|||جارٍ قراءة الدفعة…
Fichier identique déjà présent dans ce lot.|||An identical file is already in this batch.|||يوجد ملف مطابق بالفعل في هذه الدفعة.
Fichier supérieur à 25 Mo.|||File exceeds 25 MB.|||يتجاوز حجم الملف 25 ميغابايت.
Lecture interrompue ({v0}).|||Reading interrupted ({v0}).|||توقفت القراءة ({v0}).
{v0} / {v1} fichiers analysés|||{v0} / {v1} files analyzed|||تم تحليل {v0} / {v1} من الملفات
{v0} fichier(s) non importé(s). Corrigez-les ou poursuivez avec les tables disponibles.|||{v0} file(s) could not be imported. Fix them or continue with the available tables.|||تعذر استيراد {v0} ملف. صححها أو تابع بالجداول المتاحة.
{v0} table(s) disponible(s).|||{v0} table(s) available.|||عدد الجداول المتاحة: {v0}.
Fichier|||File|||الملف
Table|||Table|||الجدول
Lignes|||Rows|||الصفوف
Colonnes|||Columns|||الأعمدة
Vérification|||Review|||المراجعة
PDF à vérifier|||PDF review required|||مراجعة PDF مطلوبة
Prête|||Ready|||جاهز
Motif|||Reason|||السبب
Occurrences|||Occurrences|||عدد الحالات
Préparer les données|||Prepare data|||إعداد البيانات
Télécharger un CSV d’exemple|||Download a sample CSV|||تنزيل ملف CSV نموذجي
Composez votre recette|||Build your recipe|||أنشئ وصفة المعالجة
Sélectionnez des tables de même structure. Les identifiants restent du texte tant que vous ne changez pas leur type.|||Select tables with the same structure. Identifiers remain text unless you change their type.|||اختر جداول ذات بنية متطابقة. تبقى المعرّفات نصوصًا ما لم تغيّر نوعها.
Tables à traiter ensemble|||Tables to process together|||الجداول المراد معالجتها معًا
Sélectionnez une table pour afficher l’aperçu.|||Select a table to preview it.|||اختر جدولًا لعرض المعاينة.
Aperçu de la source|||Source preview|||معاينة المصدر
100 premières lignes au maximum · {v0} lignes dans cette table|||Up to the first 100 rows · {v0} rows in this table|||عرض أول 100 صف كحد أقصى · {v0} صف في هذا الجدول
J’ai comparé l’extraction avec le PDF : {v0} / {v1}|||I compared the extraction with the PDF: {v0} / {v1}|||قارنت البيانات المستخرجة بملف PDF: ‏{v0} / {v1}
Réutiliser une recette enregistrée|||Reuse a saved recipe|||إعادة استخدام وصفة محفوظة
Recette JSON|||JSON recipe|||وصفة JSON
Charger la recette|||Load recipe|||تحميل الوصفة
Cette recette ne correspond pas aux colonnes de la table sélectionnée.|||This recipe does not match the selected table’s columns.|||لا تتطابق هذه الوصفة مع أعمدة الجدول المحدد.
La recette actuelle correspond à une autre structure de données.|||The current recipe belongs to a different data structure.|||الوصفة الحالية تخص بنية بيانات مختلفة.
Créer une recette pour cette structure|||Create a recipe for this structure|||إنشاء وصفة لهذه البنية
Règles de préparation|||Preparation rules|||قواعد الإعداد
Nom de la recette|||Recipe name|||اسم الوصفة
Retirer les espaces en début et fin|||Trim leading and trailing spaces|||إزالة المسافات في البداية والنهاية
Marqueurs de valeurs manquantes (séparés par |)|||Missing-value markers (separated by |)|||علامات القيم المفقودة (مفصولة بالرمز |)
Les cellules vides sont toujours considérées comme manquantes. Exemple : NULL|N/A|||Empty cells are always treated as missing. Example: NULL|N/A|||تُعتبر الخلايا الفارغة قيمًا مفقودة دائمًا. مثال: NULL|N/A
Colonne source|||Source column|||عمود المصدر
Nom de sortie|||Output name|||اسم العمود الناتج
Type|||Type|||النوع
Obligatoire|||Required|||مطلوب
Remplacer les vides par|||Fill missing values with|||تعويض القيم المفقودة بـ
Casse|||Letter case|||حالة الأحرف
Conserver|||Keep|||إبقاء
Minuscules|||Lowercase|||أحرف صغيرة
Majuscules|||Uppercase|||أحرف كبيرة
Décimale|||Decimal separator|||الفاصل العشري
Format date|||Date format|||تنسيق التاريخ
Minimum|||Minimum|||الحد الأدنى
Maximum|||Maximum|||الحد الأقصى
Texte|||Text|||نص
Entier|||Integer|||عدد صحيح
Décimal|||Decimal|||عدد عشري
Date|||Date|||تاريخ
Booléen|||Boolean|||قيمة منطقية
Dates : %Y-%m-%d = 2026-01-31 ; %d/%m/%Y = 31/01/2026. Bornes numériques : point décimal. Faites défiler le tableau horizontalement pour les paramètres avancés.|||Dates: %Y-%m-%d = 2026-01-31; %d/%m/%Y = 31/01/2026. Numeric bounds use a decimal point. Scroll the table horizontally for advanced settings.|||التواريخ: %Y-%m-%d = 2026-01-31 و%d/%m/%Y = 31/01/2026. استخدم النقطة في الحدود العددية. مرّر الجدول أفقيًا لعرض الإعدادات المتقدمة.
Écarter les doublons (conserver la première ligne valide)|||Exclude duplicates (keep the first valid row)|||استبعاد التكرارات (الاحتفاظ بأول صف صالح)
Colonnes identifiant un doublon|||Columns that identify a duplicate|||الأعمدة المحددة للتكرار
Sans sélection, toutes les colonnes métier sont comparées.|||If none are selected, all business columns are compared.|||عند عدم الاختيار، تتم مقارنة جميع أعمدة البيانات.
Appliquer et contrôler|||Apply and review|||تطبيق ومراجعة
Préparation et contrôle du lot…|||Preparing and checking the batch…|||جارٍ إعداد الدفعة والتحقق منها…
Vérifiez le résultat|||Review the result|||راجع النتيجة
Appliquez votre recette pour calculer les résultats.|||Apply your recipe to calculate the results.|||طبّق الوصفة لحساب النتائج.
Recette appliquée : {v0} · résultat figé de ce traitement|||Applied recipe: {v0} · snapshot of this run|||الوصفة المطبقة: {v0} · نتيجة محفوظة لهذه العملية
Lignes sources|||Source rows|||صفوف المصدر
Lignes valides|||Valid rows|||الصفوف الصالحة
En quarantaine|||Quarantined|||الصفوف المعزولة
Doublons écartés|||Duplicates excluded|||التكرارات المستبعدة
Certaines lignes nécessitent votre attention. Elles sont conservées avec les valeurs originales et les motifs de rejet.|||Some rows need your attention. Their original values and rejection reasons are preserved.|||تحتاج بعض الصفوف إلى مراجعتك. تم الاحتفاظ بقيمها الأصلية وأسباب رفضها.
Toutes les lignes respectent les règles configurées.|||All rows meet the configured rules.|||تستوفي جميع الصفوف القواعد المحددة.
Le lot est partiel : des fichiers n’ont pas pu être importés. Ils seront signalés dans le rapport.|||This batch is partial: some files could not be imported. They will be listed in the report.|||الدفعة غير مكتملة: تعذر استيراد بعض الملفات. ستُذكر في التقرير.
Vue du résultat|||Result view|||عرض النتيجة
Données valides|||Valid data|||البيانات الصالحة
Quarantaine|||Quarantine|||الصفوف المعزولة
Qualité|||Quality|||الجودة
Traçabilité|||Traceability|||التتبع
Complétude des données valides|||Valid-data completeness|||اكتمال البيانات الصالحة
Part des cellules non vides après traitement ; ce taux ne mesure pas l’exactitude métier.|||Share of non-empty cells after processing; this does not measure business accuracy.|||نسبة الخلايا غير الفارغة بعد المعالجة؛ لا تقيس هذه النسبة صحة البيانات من منظور العمل.
Colonne|||Column|||العمود
Valeurs manquantes|||Missing values|||القيم المفقودة
Valeurs distinctes|||Distinct values|||القيم المميزة
Chaque ligne exportée porte sa source, sa table, son numéro d’enregistrement et l’empreinte du fichier.|||Each exported row includes its source, table, record number and file hash.|||يتضمن كل صف مُصدّر مصدره وجدوله ورقم سجله وبصمة ملفه.
Aperçus limités à 500 lignes. L’export contient toutes les lignes du résultat.|||Previews are limited to 500 rows. The export includes all result rows.|||المعاينة محدودة بـ500 صف. يتضمن التصدير جميع صفوف النتيجة.
Ajuster la recette|||Adjust recipe|||تعديل الوصفة
Passer à l’export|||Continue to export|||المتابعة إلى التصدير
Livrez des données traçables|||Deliver traceable data|||سلّم بيانات قابلة للتتبع
Préparez et contrôlez les données avant de les exporter.|||Prepare and review the data before exporting.|||أعدّ البيانات وراجعها قبل التصدير.
**{v0} lignes valides** · recette « {v1} »|||**{v0} valid rows** · recipe “{v1}”|||**{v0} صف صالح** · الوصفة « {v1} »
Préparer le dossier de livraison|||Prepare the delivery package|||إعداد حزمة التسليم
Format des données|||Data format|||تنسيق البيانات
CSV : UTF-8, séparateur point-virgule. Parquet : conserve les types pour vos outils d’analyse.|||CSV: UTF-8, semicolon delimiter. Parquet: preserves data types for your analytics tools.|||CSV: ترميز UTF-8 وفاصل الفاصلة المنقوطة. Parquet: يحافظ على أنواع البيانات لأدوات التحليل.
J’accepte d’exporter les lignes valides et de joindre les autres en quarantaine.|||I agree to export the valid rows and include the others in quarantine.|||أوافق على تصدير الصفوف الصالحة وإرفاق الصفوف الأخرى في ملف العزل.
J’ai pris connaissance des fichiers non importés ; je souhaite exporter ce lot partiel.|||I have reviewed the files that were not imported and want to export this partial batch.|||اطلعت على الملفات التي لم تُستورد وأرغب في تصدير هذه الدفعة الجزئية.
Générer le dossier ZIP|||Generate ZIP package|||إنشاء حزمة ZIP
Export impossible ({v0}). Essayez CSV.|||Export failed ({v0}). Try CSV.|||تعذر التصدير ({v0}). جرّب CSV.
Télécharger le dossier de livraison|||Download delivery package|||تنزيل حزمة التسليم
Dossier généré. Téléchargez-le pour le conserver.|||Package generated. Download it to keep a copy.|||تم إنشاء الحزمة. نزّلها للاحتفاظ بنسخة.
Dans votre dossier|||Inside your package|||محتويات الحزمة
- Données validées et traçables\n- Lignes en quarantaine et motifs\n- Rapport d’exécution JSON\n- Recette réutilisable\n- Instructions de lecture|||- Validated, traceable data\n- Quarantined rows and reasons\n- JSON run report\n- Reusable recipe\n- Reading instructions|||- بيانات متحقق منها وقابلة للتتبع\n- صفوف معزولة وأسباب العزل\n- تقرير تنفيذ JSON\n- وصفة قابلة لإعادة الاستخدام\n- تعليمات القراءة
Enregistrer la recette seule|||Save recipe only|||حفظ الوصفة فقط
CSV et Excel : les textes pouvant devenir des formules sont préfixés par une apostrophe.|||CSV and Excel: text that could become a formula is prefixed with an apostrophe.|||CSV وExcel: تُضاف علامة اقتباس مفردة قبل النصوص التي قد تتحول إلى صيغ.
Journal des traitements|||Run history|||سجل عمليات المعالجة
Les 20 derniers traitements de cette session. Téléchargez les rapports pour un suivi durable.|||The last 20 runs in this session. Download reports for a lasting record.|||آخر 20 عملية في هذه الجلسة. نزّل التقارير للاحتفاظ بسجل دائم.
Votre premier traitement apparaîtra ici après l’application d’une recette.|||Your first run will appear here after you apply a recipe.|||ستظهر أول عملية هنا بعد تطبيق وصفة.
{v0} lignes sources → {v1} valides · {v2} en quarantaine|||{v0} source rows → {v1} valid · {v2} quarantined|||{v0} صف مصدر ← {v1} صالح · {v2} معزول
Télécharger le rapport|||Download report|||تنزيل التقرير
Consultant en BI|||BI Consultant|||استشاري ذكاء الأعمال
Voir mon profil LinkedIn|||View my LinkedIn profile|||زيارة ملفي على LinkedIn
Ma recette|||My recipe|||وصفتي
Préparation des ventes|||Sales preparation|||إعداد بيانات المبيعات
Données|||Data|||البيانات
Numéro d’enregistrement|||Record number|||رقم السجل
Empreinte SHA-256|||SHA-256 hash|||بصمة SHA-256
Motifs de rejet|||Rejection reasons|||أسباب الرفض
"""

CATALOG = {}
for row in MESSAGES.strip().splitlines():
    fr, en, ar = row.split("|||")
    CATALOG[fr.replace(r"\n", "\n")] = {
        "fr": fr.replace(r"\n", "\n"),
        "en": en.replace(r"\n", "\n"),
        "ar": ar.replace(r"\n", "\n"),
    }
