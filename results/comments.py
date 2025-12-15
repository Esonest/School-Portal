import random

PRINCIPAL_COMMENTS = {
    'A': [
        "{name} has shown exceptional excellence this term. Keep soaring!",
        "Outstanding work by {name}. A model for peers.",
        "{name}'s dedication has produced brilliant results — well done!",
        "Impressive performance from {name}. Continue the great work!",
        "{name} is an excellent student; keep that momentum going."
    ],
    'B': [
        "{name} performed very well this term. Aim higher next time.",
        "Good effort by {name}. Keep pushing for excellence.",
        "{name}'s results are commendable — with more focus, A is close.",
        "Solid performance from {name}. Maintain the diligence.",
        "{name} is making good progress; continue working hard."
    ],
    'C': [
        "{name} had a fair term; steady improvement is required.",
        "{name} is improving; more consistency will help.",
        "Good effort from {name}; focus on weaker areas.",
        "{name} should keep practising to improve next term.",
        "{name} shows potential; more dedication will help reach goals."
    ],
    'D': [
        "{name} must put in more effort to meet expectations.",
        "Performance is below expected standard; intervention needed for {name}.",
        "{name} needs closer supervision and more practice.",
        "Encourage {name} with extra lessons to improve performance.",
        "{name} must apply greater effort to improve academically."
    ],
    'F': [
        "{name}'s performance is unsatisfactory; urgent intervention required.",
        "This result is worrying. {name} needs immediate academic support.",
        "{name} must work hard and seek help to improve.",
        "Failure is not final — {name} should focus and recover next term.",
        "Significant improvement needed from {name}. Parents and teachers should intervene."
    ],
}

TEACHER_COMMENTS = {
    'A': [
        "{name} participates actively and shows excellent understanding.",
        "Excellent comprehension in class from {name}. Keep it up!",
        "{name} consistently produces high-quality work.",
        "{name} is a pleasure to teach; outstanding results.",
        "{name} demonstrates mastery of the topics."
    ],
    'B': [
        "{name} is hardworking and performs well in lessons.",
        "{name} is focused and responds well to instruction.",
        "A good term for {name}; with a bit more effort, A is possible.",
        "{name} contributes positively in class and excels in assessments.",
        "{name} shows strong potential—keep encouraging them."
    ],
    'C': [
        "{name} is doing okay but needs to study more regularly.",
        "{name} participates but must improve revision habits.",
        "{name} has potential; more concentration in class will help.",
        "{name} should complete additional practice to improve scores.",
        "{name} needs to strengthen understanding of a few topics."
    ],
    'D': [
        "{name} needs consistent effort and supervision in studies.",
        "Extra coaching would benefit {name} greatly.",
        "{name} must prioritize learning and complete more exercises.",
        "{name} should attend extra classes for improvement.",
        "{name} needs targeted help from teachers and parents."
    ],
    'F': [
        "{name} requires urgent mentoring and remedial sessions.",
        "{name} must take academics seriously and seek help.",
        "{name} is underperforming and needs immediate attention.",
        "Extra practice and supervision are critical for {name}.",
        "{name} must improve drastically to avoid ongoing failure."
    ],
}