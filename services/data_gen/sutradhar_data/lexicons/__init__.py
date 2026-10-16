"""
Lexicons for Sutradhar synthetic data generation.

Contains Marathi/Hindi name tables with Devanagari and Roman variants,
districts, police stations, bank codes, and other reference data.

All names are ENTIRELY FICTIONAL. Any resemblance to real people is coincidental.
"""

# --------------------------------------------------------------------------- #
# SURNAMES: 45 entries with Devanagari canonical + Roman transliteration variants
# --------------------------------------------------------------------------- #
SURNAMES = [
    {"canonical_dev": "पवार", "canonical_rom": "Pawar", "variants_rom": ["Powar", "Pavar", "Pawaar"], "variants_dev": ["पोवार", "पावार"]},
    {"canonical_dev": "जाधव", "canonical_rom": "Jadhav", "variants_rom": ["Jadhao", "Jadav", "Yadav"], "variants_dev": ["जाधो", "यादव"]},
    {"canonical_dev": "शिंदे", "canonical_rom": "Shinde", "variants_rom": ["Shindey", "Shindhe", "Sindhe"], "variants_dev": ["शिंधे", "सिंधे"]},
    {"canonical_dev": "गायकवाड", "canonical_rom": "Gaikwad", "variants_rom": ["Gaekwad", "Gaikwaad", "Gaykwad"], "variants_dev": ["गाएकवाड", "गायक्वाड"]},
    {"canonical_dev": "काळे", "canonical_rom": "Kale", "variants_rom": ["Kaale", "Kaley", "Kaaley"], "variants_dev": ["काले", "कळे"]},
    {"canonical_dev": "मोरे", "canonical_rom": "More", "variants_rom": ["Morey", "Morre", "Moray"], "variants_dev": ["मोरे", "मोऱे"]},
    {"canonical_dev": "पाटील", "canonical_rom": "Patil", "variants_rom": ["Pateel", "Paatil", "Patel"], "variants_dev": ["पाटिल", "पटील"]},
    {"canonical_dev": "देशमुख", "canonical_rom": "Deshmukh", "variants_rom": ["Deshmukhey", "Deshmuk", "Desmukh"], "variants_dev": ["देशमुक", "दॆशमुख"]},
    {"canonical_dev": "कुलकर्णी", "canonical_rom": "Kulkarni", "variants_rom": ["Kulkarnee", "Kulkarny", "Colkarni"], "variants_dev": ["कुलकर्नी", "कुल्कर्णी"]},
    {"canonical_dev": "राठौर", "canonical_rom": "Rathore", "variants_rom": ["Rathor", "Raathore", "Rathod"], "variants_dev": ["राठोड", "राठोर"]},
    {"canonical_dev": "सूर्यवंशी", "canonical_rom": "Suryavanshi", "variants_rom": ["Suryawanshi", "Sooryavanshi"], "variants_dev": ["सूर्यवंशी", "सुर्यवंशी"]},
    {"canonical_dev": "भोसले", "canonical_rom": "Bhosale", "variants_rom": ["Bhosle", "Bhosaley", "Bhosley"], "variants_dev": ["भोसले", "भोसळे"]},
    {"canonical_dev": "चव्हाण", "canonical_rom": "Chavhan", "variants_rom": ["Chauhan", "Chouhan", "Chavan"], "variants_dev": ["चौहान", "चवहाण"]},
    {"canonical_dev": "सोनवणे", "canonical_rom": "Sonawane", "variants_rom": ["Sonwane", "Sonavane", "Sonavaney"], "variants_dev": ["सोनवणे", "सोनावणे"]},
    {"canonical_dev": "माने", "canonical_rom": "Mane", "variants_rom": ["Maane", "Maney", "Manay"], "variants_dev": ["मानेय", "मने"]},
    {"canonical_dev": "घाडगे", "canonical_rom": "Ghadge", "variants_rom": ["Ghadgey", "Gadge", "Ghadgay"], "variants_dev": ["घाडगे", "गडगे"]},
    {"canonical_dev": "ठोमरे", "canonical_rom": "Thomare", "variants_rom": ["Thomrey", "Tomar", "Thomare"], "variants_dev": ["ठोमरे", "तोमर"]},
    {"canonical_dev": "वाघमारे", "canonical_rom": "Waghmare", "variants_rom": ["Vagmare", "Waghmarey", "Wagmare"], "variants_dev": ["वाघमारे", "वागमारे"]},
    {"canonical_dev": "कदम", "canonical_rom": "Kadam", "variants_rom": ["Kaddam", "Kaadam", "Kadamb"], "variants_dev": ["कदम", "कदंब"]},
    {"canonical_dev": "निकम", "canonical_rom": "Nikam", "variants_rom": ["Nikamb", "Neekam", "Nikum"], "variants_dev": ["निकम", "निकुम"]},
    {"canonical_dev": "साळवे", "canonical_rom": "Salve", "variants_rom": ["Salwey", "Saalve", "Salway"], "variants_dev": ["साळवे", "सालवे"]},
    {"canonical_dev": "ढोले", "canonical_rom": "Dhole", "variants_rom": ["Doley", "Dholey", "Dhol"], "variants_dev": ["ढोले", "ढोळे"]},
    {"canonical_dev": "गोसावी", "canonical_rom": "Gosavi", "variants_rom": ["Gosawee", "Gosavey", "Goswami"], "variants_dev": ["गोसावी", "गोस्वामी"]},
    {"canonical_dev": "लोखंडे", "canonical_rom": "Lokhande", "variants_rom": ["Lokhandey", "Lokhndey", "Lokande"], "variants_dev": ["लोखंडे", "लोकंडे"]},
    {"canonical_dev": "जगताप", "canonical_rom": "Jagtap", "variants_rom": ["Jagtaap", "Jagtape", "Jagatap"], "variants_dev": ["जगताप", "जगतापे"]},
    {"canonical_dev": "ठाकूर", "canonical_rom": "Thakur", "variants_rom": ["Thakoor", "Takur", "Thakkar"], "variants_dev": ["ठाकूर", "ठक्कर"]},
    {"canonical_dev": "बोरसे", "canonical_rom": "Borse", "variants_rom": ["Borsey", "Borsay", "Borshe"], "variants_dev": ["बोरसे", "बोर्से"]},
    {"canonical_dev": "पंडित", "canonical_rom": "Pandit", "variants_rom": ["Pandeet", "Pundit", "Pandiit"], "variants_dev": ["पंडित", "पंडीत"]},
    {"canonical_dev": "शर्मा", "canonical_rom": "Sharma", "variants_rom": ["Sharmaa", "Sharmaah", "Sarma"], "variants_dev": ["शर्मा", "सर्मा"]},
    {"canonical_dev": "गुप्ता", "canonical_rom": "Gupta", "variants_rom": ["Guptaa", "Gopta", "Gupt"], "variants_dev": ["गुप्ता", "गुप्त"]},
    {"canonical_dev": "यादव", "canonical_rom": "Yadav", "variants_rom": ["Yaadav", "Jadav", "Yadaw"], "variants_dev": ["यादव", "जादव"]},
    {"canonical_dev": "वर्मा", "canonical_rom": "Verma", "variants_rom": ["Varma", "Vermaa", "Barma"], "variants_dev": ["वर्मा", "बर्मा"]},
    {"canonical_dev": "कश्यप", "canonical_rom": "Kashyap", "variants_rom": ["Kaashyap", "Kashyep", "Kasyap"], "variants_dev": ["कश्यप", "काश्यप"]},
    {"canonical_dev": "महाजन", "canonical_rom": "Mahajan", "variants_rom": ["Mahaajan", "Mahajn", "Mahajaan"], "variants_dev": ["महाजन", "महाजान"]},
    {"canonical_dev": "पारधी", "canonical_rom": "Pardhi", "variants_rom": ["Paardhi", "Pardhe", "Pardhee"], "variants_dev": ["पारधी", "पर्धी"]},
    {"canonical_dev": "खान", "canonical_rom": "Khan", "variants_rom": ["Khaan", "Kaan", "Khann"], "variants_dev": ["खान", "खानन"]},
    {"canonical_dev": "मिश्रा", "canonical_rom": "Mishra", "variants_rom": ["Misra", "Mishhra", "Misshra"], "variants_dev": ["मिश्रा", "मिसरा"]},
    {"canonical_dev": "तिवारी", "canonical_rom": "Tiwari", "variants_rom": ["Tiwaaree", "Tivari", "Tiwaari"], "variants_dev": ["तिवारी", "तिवारि"]},
    {"canonical_dev": "दुबे", "canonical_rom": "Dubey", "variants_rom": ["Dube", "Dubbey", "Dubay"], "variants_dev": ["दुबे", "दुबेय"]},
    {"canonical_dev": "चौधरी", "canonical_rom": "Chaudhary", "variants_rom": ["Chowdhary", "Choudhary", "Chaudhari"], "variants_dev": ["चौधरी", "चौधारी"]},
    {"canonical_dev": "राजपूत", "canonical_rom": "Rajput", "variants_rom": ["Raajput", "Rajpoot", "Rajputh"], "variants_dev": ["राजपूत", "राजपुत"]},
    {"canonical_dev": "नायक", "canonical_rom": "Nayak", "variants_rom": ["Naayak", "Naik", "Naaik"], "variants_dev": ["नायक", "नाईक"]},
    {"canonical_dev": "कांबळे", "canonical_rom": "Kamble", "variants_rom": ["Kambley", "Kaamble", "Kambal"], "variants_dev": ["कांबळे", "कंबळे"]},
    {"canonical_dev": "शेख", "canonical_rom": "Shaikh", "variants_rom": ["Sheikh", "Shekh", "Shaykh"], "variants_dev": ["शेख", "शैख"]},
    {"canonical_dev": "मुळे", "canonical_rom": "Mule", "variants_rom": ["Muley", "Mulay", "Mulhe"], "variants_dev": ["मुळे", "मुले"]},
]

# --------------------------------------------------------------------------- #
# FIRST NAMES: 45 entries with Devanagari canonical + Roman variants
# --------------------------------------------------------------------------- #
FIRST_NAMES = [
    {"canonical_dev": "राकेश", "canonical_rom": "Rakesh", "variants_rom": ["Raakesh", "Rakeysh"], "variants_dev": ["राकेश"], "gender": "M"},
    {"canonical_dev": "सचिन", "canonical_rom": "Sachin", "variants_rom": ["Sachinn", "Saachin"], "variants_dev": ["सचिन"], "gender": "M"},
    {"canonical_dev": "नितीन", "canonical_rom": "Nitin", "variants_rom": ["Nitinn", "Neetin", "Niteen"], "variants_dev": ["नितीन", "निटीन"], "gender": "M"},
    {"canonical_dev": "अनिल", "canonical_rom": "Anil", "variants_rom": ["Aneel", "Anill"], "variants_dev": ["अनिल", "अनील"], "gender": "M"},
    {"canonical_dev": "महेंद्र", "canonical_rom": "Mahendra", "variants_rom": ["Mahendhra", "Mahendara"], "variants_dev": ["महेंद्र", "महेन्द्र"], "gender": "M"},
    {"canonical_dev": "प्रकाश", "canonical_rom": "Prakash", "variants_rom": ["Prakaash", "Praksh"], "variants_dev": ["प्रकाश"], "gender": "M"},
    {"canonical_dev": "सुनील", "canonical_rom": "Sunil", "variants_rom": ["Suneel", "Sunill", "Suniil"], "variants_dev": ["सुनील", "सुनिल"], "gender": "M"},
    {"canonical_dev": "विजय", "canonical_rom": "Vijay", "variants_rom": ["Vijaay", "Vijey", "Bijay"], "variants_dev": ["विजय", "बिजय"], "gender": "M"},
    {"canonical_dev": "संदीप", "canonical_rom": "Sandeep", "variants_rom": ["Sandip", "Sundeep", "Sandeepp"], "variants_dev": ["संदीप", "संदिप"], "gender": "M"},
    {"canonical_dev": "रमेश", "canonical_rom": "Ramesh", "variants_rom": ["Raamesh", "Ramessh"], "variants_dev": ["रमेश"], "gender": "M"},
    {"canonical_dev": "अमित", "canonical_rom": "Amit", "variants_rom": ["Aamit", "Amith"], "variants_dev": ["अमित", "अमीत"], "gender": "M"},
    {"canonical_dev": "संजय", "canonical_rom": "Sanjay", "variants_rom": ["Sanjaay", "Sanjey"], "variants_dev": ["संजय"], "gender": "M"},
    {"canonical_dev": "राजेश", "canonical_rom": "Rajesh", "variants_rom": ["Raajesh", "Rajeysh"], "variants_dev": ["राजेश"], "gender": "M"},
    {"canonical_dev": "दीपक", "canonical_rom": "Deepak", "variants_rom": ["Dipak", "Deepack", "Diipak"], "variants_dev": ["दीपक", "दिपक"], "gender": "M"},
    {"canonical_dev": "मनोज", "canonical_rom": "Manoj", "variants_rom": ["Maanoj", "Mannoj"], "variants_dev": ["मनोज"], "gender": "M"},
    {"canonical_dev": "सुरेश", "canonical_rom": "Suresh", "variants_rom": ["Sureesh", "Suressh"], "variants_dev": ["सुरेश"], "gender": "M"},
    {"canonical_dev": "दगडू", "canonical_rom": "Dagdu", "variants_rom": ["Dagadu", "Dagdoo"], "variants_dev": ["दगडू", "दगदू"], "gender": "M"},
    {"canonical_dev": "गणेश", "canonical_rom": "Ganesh", "variants_rom": ["Ganeesh", "Gaanesh", "Gnesh"], "variants_dev": ["गणेश"], "gender": "M"},
    {"canonical_dev": "विकास", "canonical_rom": "Vikas", "variants_rom": ["Vikaas", "Vikash", "Bikash"], "variants_dev": ["विकास", "बिकास"], "gender": "M"},
    {"canonical_dev": "प्रशांत", "canonical_rom": "Prashant", "variants_rom": ["Prashanth", "Prashnt", "Prashantth"], "variants_dev": ["प्रशांत", "प्रशान्त"], "gender": "M"},
    {"canonical_dev": "अशोक", "canonical_rom": "Ashok", "variants_rom": ["Ashokk", "Aashok"], "variants_dev": ["अशोक"], "gender": "M"},
    {"canonical_dev": "किशोर", "canonical_rom": "Kishor", "variants_rom": ["Kishore", "Kishoar", "Keeshor"], "variants_dev": ["किशोर", "किशोरे"], "gender": "M"},
    {"canonical_dev": "पांडुरंग", "canonical_rom": "Pandurang", "variants_rom": ["Pandoorang", "Pandurangg"], "variants_dev": ["पांडुरंग"], "gender": "M"},
    {"canonical_dev": "बालाजी", "canonical_rom": "Balaji", "variants_rom": ["Baalaji", "Balajee"], "variants_dev": ["बालाजी", "बालजी"], "gender": "M"},
    {"canonical_dev": "दत्तात्रय", "canonical_rom": "Dattatray", "variants_rom": ["Dattatrey", "Dattatray", "Dattatreya"], "variants_dev": ["दत्तात्रय", "दत्तात्रेय"], "gender": "M"},
    {"canonical_dev": "आरती", "canonical_rom": "Aarti", "variants_rom": ["Aartee", "Arti", "Artee"], "variants_dev": ["आरती", "आर्ती"], "gender": "F"},
    {"canonical_dev": "सुषमा", "canonical_rom": "Sushma", "variants_rom": ["Sushmaa", "Sushama"], "variants_dev": ["सुषमा"], "gender": "F"},
    {"canonical_dev": "प्रतिभा", "canonical_rom": "Pratibha", "variants_rom": ["Pratibhaa", "Pratibba"], "variants_dev": ["प्रतिभा"], "gender": "F"},
    {"canonical_dev": "सविता", "canonical_rom": "Savita", "variants_rom": ["Savitaa", "Sawitaa", "Svita"], "variants_dev": ["सविता", "सवीता"], "gender": "F"},
    {"canonical_dev": "मंगल", "canonical_rom": "Mangal", "variants_rom": ["Mangall", "Mangala"], "variants_dev": ["मंगल", "मंगला"], "gender": "F"},
    {"canonical_dev": "रेखा", "canonical_rom": "Rekha", "variants_rom": ["Rekhaa", "Reka"], "variants_dev": ["रेखा"], "gender": "F"},
    {"canonical_dev": "वैशाली", "canonical_rom": "Vaishali", "variants_rom": ["Vaishalee", "Vaishaalee", "Waishali"], "variants_dev": ["वैशाली"], "gender": "F"},
    {"canonical_dev": "योगिता", "canonical_rom": "Yogita", "variants_rom": ["Yogitaa", "Yogeeta"], "variants_dev": ["योगिता", "योगीता"], "gender": "F"},
    {"canonical_dev": "अंजली", "canonical_rom": "Anjali", "variants_rom": ["Anjalee", "Anjaalee", "Anjli"], "variants_dev": ["अंजली", "अंजलि"], "gender": "F"},
    {"canonical_dev": "पूजा", "canonical_rom": "Pooja", "variants_rom": ["Puja", "Poojaa"], "variants_dev": ["पूजा", "पुजा"], "gender": "F"},
    {"canonical_dev": "हर्ष", "canonical_rom": "Harsh", "variants_rom": ["Harsha", "Harshh"], "variants_dev": ["हर्ष", "हर्षा"], "gender": "M"},
    {"canonical_dev": "ओमकार", "canonical_rom": "Omkar", "variants_rom": ["Omkaar", "Omkarr"], "variants_dev": ["ओमकार", "ॐकार"], "gender": "M"},
    {"canonical_dev": "तुषार", "canonical_rom": "Tushar", "variants_rom": ["Tushaar", "Tushhar"], "variants_dev": ["तुषार", "तुशार"], "gender": "M"},
    {"canonical_dev": "नरेंद्र", "canonical_rom": "Narendra", "variants_rom": ["Narendhra", "Narendra"], "variants_dev": ["नरेंद्र", "नरेन्द्र"], "gender": "M"},
    {"canonical_dev": "भरत", "canonical_rom": "Bharat", "variants_rom": ["Bharath", "Bharatt"], "variants_dev": ["भरत", "भारत"], "gender": "M"},
    {"canonical_dev": "यशवंत", "canonical_rom": "Yashwant", "variants_rom": ["Yeshwant", "Yashwanth", "Jashwant"], "variants_dev": ["यशवंत", "यश्वंत"], "gender": "M"},
    {"canonical_dev": "रवी", "canonical_rom": "Ravi", "variants_rom": ["Ravee", "Rawee"], "variants_dev": ["रवी", "रवि"], "gender": "M"},
    {"canonical_dev": "शैलेश", "canonical_rom": "Shailesh", "variants_rom": ["Shaileshh", "Sailesh", "Shyleesh"], "variants_dev": ["शैलेश", "शैलेष"], "gender": "M"},
    {"canonical_dev": "जयंत", "canonical_rom": "Jayant", "variants_rom": ["Jayanth", "Jayantth", "Jyant"], "variants_dev": ["जयंत", "जयन्त"], "gender": "M"},
    {"canonical_dev": "कविता", "canonical_rom": "Kavita", "variants_rom": ["Kavitaa", "Kawita"], "variants_dev": ["कविता", "कवीता"], "gender": "F"},
]

# --------------------------------------------------------------------------- #
# FATHER NAMES (a separate pool; we can also reuse first names)
# --------------------------------------------------------------------------- #
FATHER_NAMES = [
    {"canonical_dev": "दगडू", "canonical_rom": "Dagdu"},
    {"canonical_dev": "बाळकृष्ण", "canonical_rom": "Balkrishna"},
    {"canonical_dev": "रामचंद्र", "canonical_rom": "Ramchandra"},
    {"canonical_dev": "शंकर", "canonical_rom": "Shankar"},
    {"canonical_dev": "विठ्ठल", "canonical_rom": "Vitthal"},
    {"canonical_dev": "गणपत", "canonical_rom": "Ganpat"},
    {"canonical_dev": "तुकाराम", "canonical_rom": "Tukaram"},
    {"canonical_dev": "नामदेव", "canonical_rom": "Namdev"},
    {"canonical_dev": "भगवान", "canonical_rom": "Bhagwan"},
    {"canonical_dev": "ज्ञानेश्वर", "canonical_rom": "Dnyaneshwar"},
    {"canonical_dev": "मारुती", "canonical_rom": "Maruti"},
    {"canonical_dev": "बापू", "canonical_rom": "Bapu"},
    {"canonical_dev": "लक्ष्मण", "canonical_rom": "Laxman"},
    {"canonical_dev": "हरिश्चंद्र", "canonical_rom": "Harishchandra"},
    {"canonical_dev": "सदाशिव", "canonical_rom": "Sadashiv"},
    {"canonical_dev": "कृष्णा", "canonical_rom": "Krishna"},
    {"canonical_dev": "पांडुरंग", "canonical_rom": "Pandurang"},
    {"canonical_dev": "सुभाष", "canonical_rom": "Subhash"},
    {"canonical_dev": "अर्जुन", "canonical_rom": "Arjun"},
    {"canonical_dev": "दत्तात्रय", "canonical_rom": "Dattatray"},
]

# --------------------------------------------------------------------------- #
# DISTRICTS (Maharashtra)
# --------------------------------------------------------------------------- #
DISTRICTS = [
    "Thane", "Pune", "Mumbai Suburban", "Mumbai City", "Nagpur",
    "Nashik", "Aurangabad", "Kolhapur", "Solapur", "Satara",
    "Raigad", "Ratnagiri", "Sindhudurg", "Sangli", "Ahmednagar",
    "Latur", "Osmanabad", "Beed", "Jalna", "Parbhani",
    "Nanded", "Wardha", "Chandrapur", "Gadchiroli", "Dhule",
    "Jalgaon", "Buldhana", "Akola", "Amravati", "Yavatmal",
]

# --------------------------------------------------------------------------- #
# SYNTHETIC POLICE STATION NAMES (entirely fictional)
# --------------------------------------------------------------------------- #
POLICE_STATIONS = [
    "Synthetic Nagar PS", "Prabhat Colony PS", "Nutan Chowk PS",
    "Indraprast PS", "Sahyadri Vihar PS", "Godavari Gate PS",
    "Chandrakant Nagar PS", "Bahujan Colony PS", "Ajanta Road PS",
    "Sahara Heights PS", "Govind Peth PS", "Nilkantheshwar PS",
    "Pragati Nagar PS", "Shivneri Chowk PS", "Rajiv Nagar PS",
    "Bhimrao Nagar PS", "Ambedkar Colony PS", "Shivaji Marg PS",
    "Deccan PS", "Swargate PS", "Sadashiv Peth PS",
    "Kothrud PS", "Hadapsar PS", "Vashi PS",
    "Airoli PS", "Kalwa PS", "Dombivli PS",
    "Andheri PS", "Bandra PS", "Dadar PS",
]

# --------------------------------------------------------------------------- #
# BANK CODES (synthetic but valid-looking IFSCs)
# --------------------------------------------------------------------------- #
BANK_CODES = [
    {"code": "HDFC", "name": "HDFC Bank", "ifsc_prefix": "HDFC0"},
    {"code": "SBIN", "name": "State Bank of India", "ifsc_prefix": "SBIN0"},
    {"code": "ICIC", "name": "ICICI Bank", "ifsc_prefix": "ICIC0"},
    {"code": "PUNB", "name": "Punjab National Bank", "ifsc_prefix": "PUNB0"},
    {"code": "BARB", "name": "Bank of Baroda", "ifsc_prefix": "BARB0"},
    {"code": "CNRB", "name": "Canara Bank", "ifsc_prefix": "CNRB0"},
    {"code": "UBIN", "name": "Union Bank of India", "ifsc_prefix": "UBIN0"},
    {"code": "MAHB", "name": "Bank of Maharashtra", "ifsc_prefix": "MAHB0"},
    {"code": "KKBK", "name": "Kotak Mahindra Bank", "ifsc_prefix": "KKBK0"},
    {"code": "IDFB", "name": "IDFC First Bank", "ifsc_prefix": "IDFB0"},
]

# --------------------------------------------------------------------------- #
# BNS / IPC SECTIONS (synthetic law reference codes)
# --------------------------------------------------------------------------- #
CRIME_SECTIONS = {
    "EXTORTION": ["BNS-308", "BNS-309", "BNS-351"],
    "CYBER_FRAUD": ["IT-66C", "IT-66D", "BNS-318", "BNS-319"],
    "NARCOTICS": ["NDPS-21", "NDPS-22", "NDPS-29"],
    "MISSING_PERSON": ["BNS-362"],
}

# --------------------------------------------------------------------------- #
# HONORIFICS
# --------------------------------------------------------------------------- #
HONORIFICS_ROM = ["Shri", "Smt", "Mr.", "Mrs.", "Ms."]
HONORIFICS_DEV = ["श्री", "श्रीमती", "सौ.", "कु."]

# --------------------------------------------------------------------------- #
# NARRATIVE TEMPLATES (multilingual)
# --------------------------------------------------------------------------- #
NARRATIVE_TEMPLATES = {
    "FIR_mr": (
        "दिनांक {filed_date} रोजी तक्रारदार {complainant_name} यांनी {station} येथे "
        "तक्रार नोंदवली. आरोपी {accused_name} ({accused_alias}) वय {accused_age} वर्षे, "
        "रा. {accused_address}, मोबाईल क्र. {accused_phone} यांनी {crime_desc} केले. "
        "गाडी क्र. {vehicle} आणि खाते क्र. {account_no} ({bank}) याचा संबंध आहे."
    ),
    "FIR_hi": (
        "दिनांक {filed_date} को शिकायतकर्ता {complainant_name} ने {station} में "
        "शिकायत दर्ज कराई। आरोपी {accused_name} ({accused_alias}) उम्र {accused_age} वर्ष, "
        "निवासी {accused_address}, मोबाइल नं. {accused_phone} ने {crime_desc} किया। "
        "वाहन नं. {vehicle} और खाता नं. {account_no} ({bank}) से संबंधित है।"
    ),
    "FIR_en": (
        "On {filed_date}, complainant {complainant_name} filed a complaint at {station}. "
        "Accused {accused_name} ({accused_alias}), age {accused_age}, "
        "residing at {accused_address}, mobile {accused_phone}, committed {crime_desc}. "
        "Vehicle {vehicle} and account {account_no} ({bank}) are connected to the case."
    ),
    "FIR_mixed": (
        "Dated {filed_date}. Complainant {complainant_name} ने {station} येथे FIR दाखल केली. "
        "Accused {accused_name} alias {accused_alias}, age {accused_age}, "
        "address {accused_address}, phone {accused_phone}. "
        "Crime: {crime_desc}. Vehicle {vehicle}, A/C {account_no} ({bank})."
    ),
    "COMPLAINT_mr": (
        "ऑनलाइन फसवणुकीची तक्रार. तक्रारदार {complainant_name} यांचे खात्यातून "
        "रु. {amount}/- अनधिकृत हस्तांतरण झाले. प्राप्तकर्ता खाते {account_no} ({bank}). "
        "संशयित {accused_name}, फोन {accused_phone}."
    ),
    "COMPLAINT_hi": (
        "ऑनलाइन धोखाधड़ी शिकायत। शिकायतकर्ता {complainant_name} के खाते से "
        "रु. {amount}/- अनधिकृत ट्रांसफर हुआ। प्राप्तकर्ता खाता {account_no} ({bank}). "
        "संदिग्ध {accused_name}, फोन {accused_phone}."
    ),
    "COMPLAINT_en": (
        "Online fraud complaint. Complainant {complainant_name}'s account debited "
        "Rs. {amount}/- unauthorized. Beneficiary account {account_no} ({bank}). "
        "Suspect {accused_name}, phone {accused_phone}."
    ),
    "SEIZURE_mr": (
        "जप्ती अहवाल: दिनांक {filed_date}. {station} कार्यक्षेत्रात {accused_name} "
        "यांच्या ताब्यातून {seized_item} जप्त. वाहन {vehicle}. "
        "फोन {accused_phone}, पत्ता {accused_address}."
    ),
    "SEIZURE_en": (
        "Seizure report dated {filed_date}. {seized_item} seized from {accused_name} "
        "in {station} jurisdiction. Vehicle {vehicle}. "
        "Phone {accused_phone}, address {accused_address}."
    ),
    "CHARGESHEET_en": (
        "Chargesheet filed on {filed_date} at {station} following complaint by {complainant_name}. "
        "Accused {accused_name} ({accused_alias}), age {accused_age}, "
        "address {accused_address}, phone {accused_phone}. "
        "Case involves {crime_desc}. Linked account {account_no} ({bank}), "
        "vehicle {vehicle}."
    ),
}

# --------------------------------------------------------------------------- #
# CRIME DESCRIPTIONS (for narrative slot filling)
# --------------------------------------------------------------------------- #
CRIME_DESCRIPTIONS = {
    "EXTORTION": {
        "mr": "दहशत माजवून खंडणी वसूल केली",
        "hi": "धमकी देकर वसूली की",
        "en": "extortion through threats and intimidation",
    },
    "CYBER_FRAUD": {
        "mr": "ऑनलाइन फसवणूक करून पैसे हस्तांतरित केले",
        "hi": "ऑनलाइन धोखाधड़ी से पैसे ट्रांसफर किए",
        "en": "committed online fraud and transferred funds",
    },
    "NARCOTICS": {
        "mr": "अंमली पदार्थांची तस्करी केली",
        "hi": "मादक पदार्थों की तस्करी की",
        "en": "trafficking in narcotic substances",
    },
    "MISSING_PERSON": {
        "mr": "बेपत्ता व्यक्तीची तक्रार",
        "hi": "लापता व्यक्ति की शिकायत",
        "en": "report of a missing person",
    },
}

# --------------------------------------------------------------------------- #
# SEIZED ITEMS (for drug seizures)
# --------------------------------------------------------------------------- #
SEIZED_ITEMS = {
    "mr": ["५ किलो गांजा", "२ किलो चरस", "१०० ग्रॅम मेफेड्रोन", "५० ग्रॅम एमडी"],
    "en": ["5 kg ganja", "2 kg charas", "100 grams mephedrone", "50 grams MD"],
}

# --------------------------------------------------------------------------- #
# KUMBH ZONES
# --------------------------------------------------------------------------- #
KUMBH_ZONES = [
    "Ramkund", "Panchavati", "Tapovan", "Trimbakeshwar", "Godavari Ghats",
]

KUMBH_EVENT_TYPES = [
    "WATCHLIST_SIGHTING", "SCAM_PATTERN", "MISSING_PERSON",
    "MEDICAL_EMERGENCY", "CROWD_SURGE", "LOST_AND_FOUND",
    "VIP_MOVEMENT", "TRAFFIC_DIVERSION", "POWER_OUTAGE",
    "WATER_SUPPLY_ISSUE",
]
