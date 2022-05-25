//Document schema for MongoDB validation.

var word_schema=
{
  "bsonType":"array",
  "minItems":1,
  "items": {
    "required":["id","form","lemma","cpos","feat","head","deprel","misc"],
    "properties": {
      "id": {
        "bsonType":"int",
        "minimum":1
      },
      "form": {"bsonType":"string"},
      "lemma": {"bsonType":"string"},
      "cpos": {
        "bsonType":"string",
        "enum":["ADV","NOUN","PRON","PUNCT","VERB","PROPN","ADJ","AUX","CONJ","NUM","SCONJ","ADP","INTJ","X","SYM"]
      },
      "feat": {
        "bsonType":"object",
        "properties": {
          "Case": {
            "bsonType":"string",
            "enum":["Nom","Par","Gen","Acc","Ela","Ine","Ill","Abl","Ade","All","Ess","Tra","Abe","Ins","Com"]
          },
          "Degree": {
            "bsonType":"string",
            "enum":["Sup","Pos","Cmp"]
          },
          "Number": {
            "bsonType":"string",
            "enum":["Sing","Plur"]
          },
          "Number[psor]": {
            "bsonType":"string",
            "enum":["Sing","Plur"]
          },
          "Person[psor]": {
            "bsonType":"string",
            "enum":["1","2","3"]
          },
          "VerbForm": {
            "bsonType":"string",
            "enum":["Fin","Part","Inf"]
          },
          "InfForm": {
            "bsonType":"string",
            "enum":["1","2","3"]
          },
          "Mood": {
            "bsonType":"string",
            "enum":["Ind","Cnd","Imp","Pot"]
          },
          "Tense": {
            "bsonType":"string",
            "enum":["Pres","Past"]
          },
          "Voice": {
            "bsonType":"string",
            "enum":["Act","Pass"]
          },
          "token": {
            "bsonType":"string",
            "pattern":"^M\\d+$"
          },
          "Tense2": {
            "bsonType":"string",
            "enum":["Pres","Impf","Perf","Pperf","Kond","Kperf","Pot","Potperf","Impr","Inf"]
          },
          "Voice2": {
            "bsonType":"string",
            "enum":["Act","Pass","Null"]
          },
          "Sign2": {
            "bsonType":"string",
            "enum":["+","-"]
          },
          "Person2": {
            "bsonType":"string",
            "enum":["1","2","3","Null"]
          },
          "Number2": {
            "bsonType":"string",
            "enum":["Sing","Plur","Null"]
          },
          "InfForm2": {
            "bsonType":"string",
            "enum":["1","2","3","5"]
          },
          "PartForm": {
            "bsonType":"string",
            "enum":["Past","Agt","Pres","Neg"]
          },
          "AdpType": {
            "bsonType":"string",
            "enum":["Prep","Post"]
          },
          "NumType": {
            "bsonType":"string",
            "enum":["Card","Ord"]
          },
          "PronType": {
            "bsonType":"string",
            "enum":["Dem","Rel","Prs","Ind","Int","Rcp"]
          },
          "Reflex": {
            "bsonType":"string",
            "enum":["Yes"]
          },
          "Connegative": {
            "bsonType":"string",
            "enum":["Yes"]
          },
          "Negative": {
            "bsonType":"string",
            "enum":["Yes"]
          },
          "Foreign": {
            "bsonType":"string",
            "enum":["Foreign"]
          },
          "Abbr": {
            "bsonType":"string",
            "enum":["Yes"]
          },
          "Typo": {
            "bsonType":"string",
            "enum":["Yes"]
          },
          "Derivation": {
            "bsonType":"string",
            "enum":["Inen","Ja","Lainen","Llinen","Minen","Sti","Tar","Ton","Ttaa","Ttain","U","Vs"]
          },
          "Clitic": {
            "oneOf": [{
              "bsonType":"string",
              "enum":["Han","Pa","Ka","Ko","Kin","Kaan","S"]
            },
            {
              "bsonType":"array",
              "minItems":2,
              "items": {
                "bsonType":"string",
                "enum":["Han","Pa","Ka","Ko","Kin","Kaan","S"]
              }
            }]
          }
        },
        "dependencies": {
          "InfForm": {
            "required":["VerbForm"],
            "properties": {"VerbForm": {"enum":["Inf"]}}
          },
//a 5th infinitive form may not even get a VerbForm, so this might fail
          //"InfForm2": {
          //  "required":["VerbForm","token"],
          //  "properties": {"VerbForm": {"enum":["Inf"]}}
          //},
          "Tense2": {"required":["token"]},
          "Voice2": {"required":["token"]},
          "Number2": {"required":["token"]},
          "Sign2": {"required":["token"]},
          "Person2": {"required":["token"]},
          "PartForm": {
            "required":["VerbForm"],
            "properties": {"VerbForm": {"enum":["Part"]}}
          }
        }
//some of these could be required to follow VerbForm=Fin
      },
      "head": {
        "bsonType":"int",
        "minimum":0
      },
      "deprel": {
        "bsonType":"string",
        "enum":["acl:relcl","advmod","det","nmod","nsubj","punct","root","ccomp","nmod:poss","cop","nsubj:cop","advcl","amod","aux","cc","conj","dobj","mark","neg","nmod:own","nummod","compound:nn","mwe","name","case","xcomp","acl","appos","nmod:gobj","discourse","remnant","compound","xcomp:ds","parataxis","auxpass","nmod:gsubj","csubj:cop","csubj","vocative","compound:prt","cc:preconj","goeswith","dep"]
      },
      "misc": {
        "bsonType":"string",
        "pattern":"^\\d+(\\.\\d+)*$"
      }
    }
  }
};

var ptk_schema={
  "required":["words","sentence","text","metadata"],
  "properties": {
    "sentence": {
      "bsonType":"int",
      "minimum":1,
      "maximum":9999
    },
    "text": {"bsonType":"string"},
    "words": word_schema,
    "metadata": {
      "bsonType":"object",
      "required": ["vp","inro","date"],
      "properties": {
        "inro": {
          "bsonType":"int",
          "minimum":1
        },
        "vp": {
          "bsonType":"int",
          "minimum":1907
        },
        "paragraph": {
          "bsonType":"int",
          "minimum":1
        },
        "sukunimi": {"bsonType":"string"},
        "etunimi": {"bsonType":"string"},
        "ekryhma": {"bsonType":"string"},
        "gov": {"bsonType":"bool"},
        "asema": {"bsonType":"string"},
        "date": {"bsonType":"date"},
        "page": {
          "bsonType":"int",
          "minimum":1
        },
        "pnro": {
          "bsonType":"int",
          "minimum":1
        },
        "pjnro": {
          "bsonType":"int",
          "minimum":1
        },
        "asia": {"bsonType":"string"},
        "sasia": {"bsonType":"string"},
        "kieli": {"bsonType":"string"},
        "numero": {"bsonType":"int"},
        "snoviite": {"bsonType":"int"},
        "tyyppi": {"bsonType":"string"},
        "ptkviite": {"bsonType":"string"},
        "aktyyppi": {"bsonType":"string"},
        "akviite": {"bsonType":"string"},
        "tila": {"bsonType":"string"},
        "versio": {
          "bsonType":"string",
          "pattern":"\\d\\.\\d{1,2}"
        }
      }
    }
  }
};
