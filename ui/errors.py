"""Translations for engine diagnostics; the engine keeps its stable French messages."""

MESSAGES = r"""
Limite dépassée : 100 000 lignes ou 300 colonnes par table.|||Limit exceeded: 100,000 rows or 300 columns per table.|||تم تجاوز الحد: 100,000 صف أو 300 عمود لكل جدول.
Les en-têtes doivent être présents et non vides.|||Headers must be present and non-empty.|||يجب أن تكون عناوين الأعمدة موجودة وغير فارغة.
En-têtes en double : renommez-les dans le fichier source.|||Duplicate headers: rename them in the source file.|||عناوين أعمدة مكررة: أعد تسميتها في الملف المصدر.
Le préfixe _etl_ est réservé à la traçabilité.|||The _etl_ prefix is reserved for traceability.|||البادئة _etl_ مخصصة للتتبع.
Le fichier est vide.|||The file is empty.|||الملف فارغ.
Le fichier dépasse 25 Mo.|||The file exceeds 25 MB.|||يتجاوز حجم الملف 25 ميغابايت.
Format .{v0} non pris en charge.|||Format .{v0} is not supported.|||التنسيق .{v0} غير مدعوم.
Séparateur non pris en charge.|||Unsupported delimiter.|||الفاصل غير مدعوم.
Aucun en-tête dans le fichier.|||No header found in the file.|||لا يوجد صف عناوين في الملف.
Enregistrement {v0} : {v1} champs au lieu de {v2}.|||Record {v0}: {v1} fields instead of {v2}.|||السجل {v0}: عدد الحقول {v1} بدلًا من {v2}.
Limite de 100 000 lignes dépassée.|||The 100,000-row limit was exceeded.|||تم تجاوز حد 100,000 صف.
JSON attendu : liste d’objets. Indiquez le chemin vers cette liste si nécessaire.|||Expected JSON: a list of objects. Specify the path to that list if needed.|||تنسيق JSON المتوقع: قائمة كائنات. حدد المسار إلى هذه القائمة عند الحاجة.
Classeur décompressé trop volumineux (limite 200 Mo).|||Uncompressed workbook is too large (200 MB limit).|||حجم المصنف بعد فك الضغط كبير جدًا (الحد 200 ميغابايت).
La ligne d’en-tête doit être comprise entre 1 et 100.|||The header row must be between 1 and 100.|||يجب أن يكون رقم صف العناوين بين 1 و100.
Maximum 50 feuilles par classeur.|||Maximum 50 sheets per workbook.|||الحد الأقصى 50 ورقة لكل مصنف.
Feuille {v0} : ligne d’en-tête absente.|||Sheet {v0}: header row missing.|||الورقة {v0}: صف العناوين غير موجود.
Maximum 100 pages PDF.|||Maximum 100 PDF pages.|||الحد الأقصى 100 صفحة PDF.
Maximum 50 tables PDF.|||Maximum 50 PDF tables.|||الحد الأقصى 50 جدولًا في PDF.
Aucune table détectée. Les PDF scannés nécessitent un OCR, non inclus dans cette version.|||No table detected. Scanned PDFs require OCR, which is not included in this version.|||لم يُكتشف أي جدول. تتطلب ملفات PDF الممسوحة ضوئيًا التعرف الضوئي على الحروف، وهو غير متاح في هذا الإصدار.
Aucune table exploitable dans ce fichier.|||No usable table found in this file.|||لا يوجد جدول قابل للاستخدام في هذا الملف.
Lecture impossible ({v0}). Vérifiez le format et les paramètres d’import.|||Unable to read the file ({v0}). Check its format and import settings.|||تعذرت قراءة الملف ({v0}). تحقق من التنسيق وإعدادات الاستيراد.
Version de recette non prise en charge (version 1 attendue).|||Unsupported recipe version (version 1 required).|||إصدار الوصفة غير مدعوم (الإصدار 1 مطلوب).
Donnez un nom à la recette.|||Enter a recipe name.|||أدخل اسمًا للوصفة.
Schéma attendu invalide.|||Invalid expected schema.|||بنية الأعمدة المتوقعة غير صالحة.
Une règle est nécessaire pour chaque colonne.|||Each column needs a rule.|||كل عمود يحتاج إلى قاعدة.
Les règles doivent correspondre aux colonnes attendues, dans le même ordre.|||Rules must match the expected columns in the same order.|||يجب أن تتطابق القواعد مع الأعمدة المتوقعة وبالترتيب نفسه.
Noms de sortie invalides ou réservés.|||Output names are invalid or reserved.|||أسماء الأعمدة الناتجة غير صالحة أو محجوزة.
Deux colonnes ne peuvent pas avoir le même nom de sortie.|||Two columns cannot share the same output name.|||لا يمكن أن يحمل عمودان اسم الناتج نفسه.
Les marqueurs de valeurs manquantes doivent être une liste de textes.|||Missing-value markers must be a list of strings.|||يجب أن تكون علامات القيم المفقودة قائمة نصوص.
Paramètre booléen invalide : {v0}.|||Invalid boolean parameter: {v0}.|||معامل منطقي غير صالح: {v0}.
Clé de dédoublonnage inconnue.|||Unknown deduplication key.|||مفتاح إزالة التكرار غير معروف.
Type ou transformation de texte invalide.|||Invalid type or text transformation.|||نوع أو تحويل نصي غير صالح.
Le contrôle obligatoire doit être booléen.|||The required-field setting must be boolean.|||يجب أن يكون إعداد الحقل المطلوب قيمة منطقية.
Paramètres de colonne incomplets.|||Incomplete column settings.|||إعدادات العمود غير مكتملة.
Séparateur décimal invalide.|||Invalid decimal separator.|||الفاصل العشري غير صالح.
Un format de date explicite est obligatoire.|||An explicit date format is required.|||يجب تحديد تنسيق تاريخ صريح.
Les bornes doivent être numériques (point décimal).|||Bounds must be numeric (decimal point).|||يجب أن تكون الحدود عددية (باستخدام النقطة العشرية).
Les bornes finies sont réservées aux colonnes numériques.|||Finite bounds are only supported for numeric columns.|||الحدود العددية المنتهية متاحة للأعمدة العددية فقط.
La borne minimale dépasse la borne maximale.|||The minimum bound exceeds the maximum.|||الحد الأدنى يتجاوز الحد الأقصى.
La recette dépasse 1 Mo.|||The recipe exceeds 1 MB.|||يتجاوز حجم الوصفة 1 ميغابايت.
Recette JSON illisible.|||Unable to read the JSON recipe.|||تعذرت قراءة وصفة JSON.
Sélectionnez au moins une table.|||Select at least one table.|||اختر جدولًا واحدًا على الأقل.
Le lot dépasse 100 000 lignes. Traitez-le en plusieurs lots.|||The batch exceeds 100,000 rows. Split it into smaller batches.|||تتجاوز الدفعة 100,000 صف. قسّمها إلى دفعات أصغر.
Vérifiez l’extraction PDF avant de poursuivre : {v0} / {v1}.|||Review the PDF extraction before continuing: {v0} / {v1}.|||راجع البيانات المستخرجة من PDF قبل المتابعة: ‏{v0} / {v1}.
Schéma incompatible : {v0} / {v1}. Choisissez des tables de même structure.|||Incompatible schema: {v0} / {v1}. Choose tables with the same structure.|||بنية غير متوافقة: ‏{v0} / {v1}. اختر جداول ذات بنية متطابقة.
{v0} : valeur obligatoire|||{v0}: required value|||{v0}: قيمة مطلوبة
{v0} : conversion {v1} impossible|||{v0}: cannot convert to {v1}|||{v0}: تعذر التحويل إلى {v1}
{v0} : hors borne {v1}|||{v0}: outside {v1} bound|||{v0}: خارج الحد {v1}
{v0} : format de date invalide.|||{v0}: invalid date format.|||{v0}: تنسيق التاريخ غير صالح.
{v0} : date invalide ({v1})|||{v0}: invalid date ({v1})|||{v0}: تاريخ غير صالح ({v1})
{v0} : booléen invalide|||{v0}: invalid boolean|||{v0}: قيمة منطقية غير صالحة
Doublon : première ligne valide conservée|||Duplicate: first valid row kept|||تكرار: تم الاحتفاظ بأول صف صالح
Confirmez l’export des seules lignes valides ; les autres seront jointes en quarantaine.|||Confirm exporting only valid rows; the remaining rows will be included in quarantine.|||أكد تصدير الصفوف الصالحة فقط؛ ستُرفق الصفوف الأخرى في ملف العزل.
Format de sortie inconnu.|||Unknown output format.|||تنسيق الناتج غير معروف.
Aucune ligne valide à exporter.|||No valid rows to export.|||لا توجد صفوف صالحة للتصدير.
"""
