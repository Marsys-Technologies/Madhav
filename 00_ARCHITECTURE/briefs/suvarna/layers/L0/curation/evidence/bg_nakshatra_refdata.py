# Reference tables transcribed BY HAND from chunk text read in this session (chunk ids in comments)
NAMES={1:'Ashwini',2:'Bharani',3:'Krittika',4:'Rohini',5:'Mrigasira',6:'Ardra',7:'Punarvasu',8:'Pushya',9:'Ashlesha',10:'Magha',11:'Purva Phalguni',12:'Uttara Phalguni',13:'Hasta',14:'Chitra',15:'Swati',16:'Vishakha',17:'Anuradha',18:'Jyeshtha',19:'Moola',20:'Purva Ashadha',21:'Uttara Ashadha',22:'Shravana',23:'Dhanishtha',24:'Shatabhisha',25:'Purva Bhadrapada',26:'Uttara Bhadrapada',27:'Revati',28:'Abhijit'}
# bphs_pg0500_c01 Table of Dasas (groups in printed order Sun,Moon,Mars,Rahu,Jupiter,Saturn,Mercury,Ketu,Venus)
BPHS_LORD={}
for lord,ids in {'sun':[3,12,21],'moon':[4,13,22],'mars':[5,14,23],'rahu':[6,15,24],'jupiter':[7,16,25],'saturn':[8,17,26],'mercury':[9,18,27],'ketu':[10,19,1],'venus':[11,20,2]}.items():
    for i in ids: BPHS_LORD[i]=lord
# bphs_pg0501_c01/c02 + bphs_pg0502_c01 rasi->nakshatra table
BPHS_RASHI={1:['Aries'],2:['Aries'],3:['Aries','Taurus'],4:['Taurus'],5:['Taurus','Gemini'],6:['Gemini'],7:['Gemini','Cancer'],8:['Cancer'],9:['Cancer'],10:['Leo'],11:['Leo'],12:['Leo','Virgo'],13:['Virgo'],14:['Virgo','Libra'],15:['Libra'],16:['Libra','Scorpio'],17:['Scorpio'],18:['Scorpio'],19:['Sagittarius'],20:['Sagittarius'],21:['Sagittarius','Capricorn'],22:['Capricorn'],23:['Capricorn','Aquarius'],24:['Aquarius'],25:['Aquarius','Pisces'],26:['Pisces'],27:['Pisces']}
# muhurta_chintamani_pg0095_c01 (verse 29)
MC_GANA={}
for g,ids in {'Rakshasa':[10,9,23,18,19,24,3,14,16],'Manushya':[11,20,25,12,21,26,4,2,6],'Deva':[17,7,5,22,27,15,1,8,13]}.items():
    for i in ids: MC_GANA[i]=g
# muhurta_chintamani_pg0094_c01 (verses 25-26 tika)
MC_YONI={1:'horse',24:'horse',15:'buffalo',13:'buffalo',23:'lion',25:'lion',2:'elephant',27:'elephant',8:'sheep(mesha)',3:'sheep(mesha)',22:'monkey',20:'monkey',21:'mongoose',28:'mongoose',4:'serpent',5:'serpent',18:'deer(harina)',17:'deer(harina)',19:'dog',6:'dog',7:'cat',9:'cat',10:'rat',11:'rat',16:'tiger',14:'tiger',12:'cow',26:'cow'}
YONI_MAP={'horse':'Horse','buffalo':'Buffalo','lion':'Lion','elephant':'Elephant','sheep(mesha)':'Goat','monkey':'Monkey','mongoose':'Mongoose','serpent':'Serpent','deer(harina)':'Hare','dog':'Dog','cat':'Cat','rat':'Rat','tiger':'Tiger','cow':'Cow'}
# muhurta_chintamani_pg0096_c02 + pg0097_c01 (verse 34 + tika); 'each with its pair' = named star + the following star (inference)
MC_NADI={}
for n,ids in {'Adi':[1,6,7,12,13,18,19,24,25],'Madhya':[8,5,14,17,2,23,20,11,26],'Antya':[15,16,3,4,9,10,21,22,27]}.items():
    for i in ids: MC_NADI[i]=n
NADI_NAMED_HEAD={1,6,12,18,24, 8,5,14,17,2,23,20,11,26, 15,3,9,21,27}  # stated by name; remainder = the 'pair' star
# muhurta_chintamani_pg0037_c02 (verses 2-5) + pg0038_c01 (verses 6-8 + tika)
MC_TYPE={}
for t,ids in {'Dhruva':[12,21,26,4],'Chara':[15,7,22,23,24],'Ugra':[11,20,25,2,10],'Mishra':[16,3],'Kshipra/Laghu':[13,1,8,28],'Mridu':[5,27,14,17],'Tikshna':[19,18,6,9]}.items():
    for i in ids: MC_TYPE[i]=t
# muhurta_chintamani_pg0036_c01 verse 1 + tika  : (mc_text, kind) kind D=same name, S=synonym/equivalence step
MC_DEITY={1:('Ashvini Kumara (Nasatya)','D'),2:('Yama (Antaka)','D'),3:('Agni (Vahni)','D'),4:('Brahma (Dhatr)','D'),5:('Chandra (Shashabhrit)','S'),6:('Shiva (Rudra)','S'),7:('Aditi','D'),8:('ijya = Jupiter (verse; OCR-joined)','S'),9:('uraga = serpent (verse; OCR-joined)','S'),10:('Pitarah (verse)','D'),11:('Bhaga','D'),12:('Aryama','D'),13:('Surya/Ravi','S'),14:('Vishvakarma (Tvashta)','D'),15:('Vayu (Sameera)','D'),16:('Indra and Agni','D'),17:('Mitra','D'),18:('Indra','D'),19:('Nirriti','D'),20:('Jala (water)','S'),21:('Vishvedeva','D'),22:('Vishnu (Govinda)','D'),23:('Vasu','D'),24:('Varuna (Toya)','D'),25:('Ajacharana','S'),26:('Ahirbudhnya','D'),27:('Pushan','D'),28:('Vidhi = Brahma','S')}
# muhurta_chintamani_pg0054_c02 / pg0055_c01 forms ('aśvinyādikānāṃ rūpa'): (mc form, match_kind) ; match: M direct, I inference, X differs
MC_FORM={1:('horse-like face','M'),2:('bhaga (yoni)','M'),3:('kshura (razor)','M'),4:('gadi (cart)','M'),5:('harina-mukha (deer face)','M'),6:('mani (gem)','I'),7:('makan (house)','X'),8:('baan (arrow)','X'),9:('chakra (wheel)','X'),10:('makan (house)','X'),11:('mancha (couch)','M'),12:('bistar (bed)','M'),13:('hast (hand)','M'),14:('moti (pearl)','M'),15:('munga (coral)','M'),16:('torana (arch)','M'),17:('bhat ka punj (heap of cooked rice)','X'),18:('kundala (earring)','M'),19:('sher ki poonchh (lion tail)','X'),20:('hathi-dant (elephant tusk)','M'),21:('mancha (couch)','X'),22:('vamana / tricharana (three feet)','I'),23:('mridanga (drum)','M'),24:('vritta (circle)','M'),25:('mancha (couch/cot)','M'),26:('yamala (twin)','M'),27:('mardala/mridanga-like (drum)','I'),28:('trikona (triangle) [abbr. a.]','I')}
# muhurta_chintamani_pg0055_c01 syllable chart: printed token -> (db-equivalent expected, quality)
MC_AKS={1:('चूचेचोखा','Chu Che Cho La','legible'),2:('लील्रैको','Li Lu Le Lo','legible'),3:('आईॐर','A I U E','partial'),4:('ओवन','O Va Vi Vu','partial'),5:('वेवोकराकी','Ve Vo Ka Ki','legible'),6:('कूघङ्छ','Ku Gha Nga Chha','legible'),7:('केकादाही','Ke Ko Ha Hi','partial'),8:('हटदोडा','Hu He Ho Da','partial'),10:('मामीनूमे','Ma Mi Mu Me','legible'),12:('टेदोपापी','Te To Pa Pi','legible'),13:('पूषाणाठा','Pu Sha Na Tha','legible'),14:('पेपोरारी','Pe Po Ra Ri','legible'),15:('रूरेरोता','Ru Re Ro Ta','legible'),16:('तीतूतेतो','Ti Tu Te To','legible'),17:('नानीनून','Na Ni Nu Ne','legible'),18:('नोयायीय्','No Ya Yi Yu','legible'),20:('भूधाफाटा','Bhu Dha Pha Dha','legible'),21:('भेभोजाजी','Bhe Bho Ja Ji','legible'),22:('खीखूखेश्वा','Khi Khu Khe Kho','legible'),23:('गागीगूगे','Ga Gi Gu Ge','legible'),24:('जौरासी','Go Sa Si (Su)','partial')}
