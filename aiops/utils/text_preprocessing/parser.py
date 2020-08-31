import re


class Email:
    """
        whole_email_body: is the email content (whole body - including salutation/signature/email track etc). It must be lower-case
    """

    # Aman may do in future: Convert this utils into static utils and these parameters needs to be passed to parse_text static factory method only
    def __init__(self, whole_email_body, content_type="text", add_signature_regex=[]) -> None:
        super().__init__()
        if whole_email_body is None:
            raise ValueError("'whole_email_body' can't be 'None'....")
        self._whole_email_body = whole_email_body.strip()
        self._content_type = content_type
        self._salutation = None
        self._body = None
        self._body_without_signature = None
        self._signature = None
        self._trailing_emails_entire_text = None
        EmailParserProperties.signature_regex.extend(add_signature_regex)
        if content_type == "html":
            # Aman may do in future: It could magically identify the separater line to trim-out trailing emails
            pass
        elif content_type == "text":
            pass

    def parse_text(self):
        self._parse_salutation()
        self._parse_body(check_signature=False)
        self._parse_body()
        self._parse_signature_and_trailing_emails()
        return self.Inner(self._salutation, self._body, self._signature, self._trailing_emails_entire_text)

    def _get_trailing_emails_content(self, content_starting_with_signature):
        """
        Scenarios covered:
            1. Gmail: "On May 16, 2011, Dave wrote:"
            2. Outlook: "From: Some Person [some.person@domain.tld]"
            3. Others: "From: Some Person\nSent: 16/05/2011 22:42\nTo: Some Other Person"
            4. Forwarded / FYI
            5. Patterns: "From: <email@domain.tld>\nTo: <email@domain.tld>\nDate:<email@domain.tld"
            6. Patterns: "From:, To:, Sent:"
            7. Patterns: "Original Message"
        :param content_starting_with_signature:
        :return:
        """
        pattern = "(?P<trailing_emails_content>" + "|".join(EmailParserProperties.trailing_emails_content) + ")"
        groups = re.search(pattern, content_starting_with_signature, re.IGNORECASE + re.DOTALL)
        trailing_emails_content = None
        if groups is not None:
            if "trailing_emails_content" in groups.groupdict():
                trailing_emails_content = groups.groupdict()["trailing_emails_content"]
        return trailing_emails_content if trailing_emails_content is None else trailing_emails_content.strip()

    def _parse_signature_and_trailing_emails(self):
        signature = ""
        temp_content = self._whole_email_body
        self._trailing_emails_entire_text = self._get_trailing_emails_content(temp_content)
        temp_content = temp_content[: temp_content.find(self._trailing_emails_entire_text)] if self._trailing_emails_entire_text is not None else temp_content
        if self._signature is None:
            # Aman may do in future: Need to cater simple FYI emails and simple forward emails
            if self._salutation is None:
                self._parse_salutation()
            if self._salutation:
                temp_content = temp_content[len(self._salutation):]
            pattern = "(?P<signature>(" + "|".join(EmailParserProperties.signature_regex) + ")(.)*)"
            groups = re.search(pattern, temp_content, re.IGNORECASE + re.DOTALL)
            if groups:
                if "signature" in groups.groupdict():
                    signature = groups.groupdict()["signature"]

                    # If signature has another signature within, it means we might have included contents of body in the signature
                    # However, trailing_emails_entire_text is ok even then
                    tmp_signature_current_content = signature
                    tmp_signature_previous_content = tmp_signature_current_content
                    for s in EmailParserProperties.signature_regex:
                        search_results = re.finditer(s, tmp_signature_current_content, re.IGNORECASE)
                        for search_result in search_results:
                            starting_index = search_result.span()[0] if search_result else -1
                            tmp_signature_current_content = tmp_signature_current_content[starting_index:]
                    groups = re.search(pattern, tmp_signature_current_content, re.IGNORECASE + re.DOTALL)
                    if groups:
                        signature_temp = groups.groupdict()["signature"]
                        if abs(len(signature) - len(signature_temp)) > 22:
                            signature = signature_temp

            # Aman may do in future: How to cater if still not able to find signature
            if not signature:
                pass

            # check to see if the entire body of the message has been 'stolen' by the signature. If so, return no sig so body can have it.
            if self._body_without_signature is not None and signature.strip() == self._body_without_signature:
                if self._salutation is not None and re.search("thank", self._salutation, re.IGNORECASE):
                    self._body = self._salutation
                    self._salutation = None
                else:
                    signature = None

            self._signature = signature if signature is None else signature.strip()

        return self._signature

    def _parse_body(self, check_salutation=True, check_signature=True, check_reply_text=True, check_zone=None):
        # Aman may do in future: check_zone needs to be implemented
        if (self._body is None and check_signature) or (self._body_without_signature is None and not check_signature):
            temp_content = self._whole_email_body
            if check_salutation:
                if self._salutation:
                    temp_content = self._whole_email_body[len(self._salutation):]
            if check_reply_text:
                reply_text = self._get_trailing_emails_content(temp_content)
                if reply_text:
                    temp_content = temp_content[:temp_content.find(reply_text)]
            if check_signature:
                sig = self._parse_signature_and_trailing_emails()
                if sig:
                    temp_content = temp_content[:temp_content.find(sig)]
            if check_signature:
                if not self._body:
                    self._body = temp_content if temp_content is None else temp_content.strip()
            else:
                self._body_without_signature = temp_content if temp_content is None else temp_content.strip()

    def _parse_salutation(self):
        if self._salutation is None:
            temp_content = self._whole_email_body
            reply_text = self._get_trailing_emails_content(temp_content)
            if reply_text:
                temp_content = self._whole_email_body[:self._whole_email_body.find(reply_text)]
            salutation = None
            pattern = "\s*(?P<salutation>(" + "|".join(EmailParserProperties.salutation_regex) + r")+([^\.,\xe2:\n]*\w*){0,4}[\.,\xe2:\n]+\s*)"
            groups = re.match(pattern, temp_content, re.IGNORECASE)
            if groups is not None:
                if "salutation" in groups.groupdict():
                    salutation = groups.groupdict()["salutation"]
            self._salutation = salutation if salutation is None else salutation.strip()

    class Inner:

        def __init__(self, salutation, body, signature, trailing_emails_entire_text) -> None:
            super().__init__()
            self._salutation = salutation
            self._body = body
            self._signature = signature
            self._trailing_emails_entire_text = trailing_emails_entire_text

        def get_salutation(self):
            return self._salutation

        def get_body(self):
            return self._body

        def get_signature(self):
            return self._signature

        def get_trailing_emails_entire_text(self):
            return self._trailing_emails_entire_text


class EmailParserProperties:
    salutation_regex = [
        r"hi+",
        r"dear{1,2}",
        r"to",
        r"hey{1,2}",
        r"hello{0,2}",
        # r"thanks?",
        # r"thanks *a[ \-\s_:\)\(\]\[]*(lot|ton)",
        # r"a* *thank[ \-\s_:\)\(\]\[]+you"
        r"a*[ \-\s_:\)\(\]\[]*good[ \-\s_:\)\(\]\[]+morning",
        r"a*[ \-\s_:\)\(\]\[]*good[ \-\s_:\)\(\]\[]+afternoon",
        r"a*[ \-\s_:\)\(\]\[]*good[ \-\s_:\)\(\]\[]+evening",
        r"greetings",
        # r"okay,? ?thanks?-?y?o?u?",
    ]

    signature_regex = [
        "(?<!(Thanks & |anks and ))warms? *regards?",
        "(?<!(Thanks & |anks and ))kinds? *regards?",
        "(?<!(Thanks & |anks and ))bests? *regards?",
        "many thanks",
        "thank[ -]?you",
        "thanks? (and|&) regards?",
        "talk[ -]?soo?n?",
        "yours *truly",
        "thanki?n?g? you",
        "sent from my iphone",
        "b?rgds?[^ing]"
        "ciao",
        "(?<!([\n\s]many|great) )thanks?",
        "with ?t?h?e? ?h?i?g?h?e?s?t? ?regards?",
        "(?<!(\w and|\w{3} &|\w{2}  &|[\n\s]with|kinds|[\n\s]kind|bests|[\n\s]best) )regards?[^ing]",
        "cheers",
        "cordially",
        "cordialement",
        "sincerely",
        "greetings?",
    ]

    trailing_emails_content = [
        r"\**on\** *[a-z0-9, :/<>@\.\"\[\]]* wrote\:.*",
        r"\**from\**[\n ]*:[\n ]*[\w@ \.]* ?([\[\(]?mailto:[\w\.]*@[\w\.]*[\)\]]?)?.*",
        r"\**from\**: [\w@ \.]*(\n|\r\n)+sent: [\*\w@ \.,:/]*(\n|\r\n)+to:.*(\n|\r\n)+.*",
        r"\**from\**: ?[\w@ \.]*(\n|\r\n)+sent: [\*\w@ \.,:/]*(\n|\r\n)+to:.*(\n|\r\n)+.*",
        r"sent: [\*\w@ \.,:/]*(\n|\r\n)+to:.*(\n|\r\n)+.*",
        r"\**[- ]*forwarded by [\w@ \.,:/]*.*",
        r"\**from\**: [\w@ \.<>\-]*(\n|\r\n)to: [\w@ \.<>\-]*(\n|\r\n)date: [\w@ \.<>\-:,]*\n.*",
        r"\**from\**: [\w@ \.<>\-]*(\n|\r\n)to: [\w@ \.<>\-]*(\n|\r\n)sent: [\*\w@ \.,:/]*(\n|\r\n).*",
        r"\**from\**: [\w@ \.<>\-]*(\n|\r\n)to: [\w@ \.<>\-]*(\n|\r\n)subject:.*",
        r"(-| )*original message(-| )*.*"
    ]


if __name__ == "__main__":
    obj = Email("""
    
Hello Heba Kamel / Allaa / Nariman /all,
Good Morning ,
Kindly note that Allaa Khaleel gratefully accepted to support this migration on the new TW : SAT 22 AUG @ 12 pm GMT.
Thanks in advance
Original Appointment 
From: KHASHABA Ahmed OBS/CSO On Behalf Of KAMEL Heba OBS/CSO
Sent: Thursday, August 20, 2020 10:44
To: KHALEEL Allaa OBS/CSO (allaa.khaleel@orange.com); SAUDI Nariman OBS/CSO
Subject: FW: Fw:BAT Migration of ROBC01 (Romania Bucharest Business Park Category 2 /Option 5) CH4429354 >>>>>>>> Planned for 22nd Aug, 6:00 AM GMT
When: Saturday, August 22, 2020 08:00 17:00 (UTC pplluuss 02:00) Cairo.
Where: webex
Hello Allaa / Nariman ,
Good Morning ,
Thanks to book that slot in your calendar for the Migration of ROBC01 (Romania Bucharest Business Park Category 2 /Option 5) CH4429354 >>> Planned for 22nd Aug, 6:00 AM GMT
Thanks in advance 
Original Appointment 
From: KAMEL Heba OBS/CSO 
Sent: Wednesday, August 19, 2020 16:23
To: KAMEL Heba OBS/CSO; ZZZ ECS VPI EMEA Demands; Dorio_Popenta@bat.com; ADRIAN NEACSA (Adrian_Neacsa@bat.com);
gary_clements@bat.com; Srdjan_Jeisel@bat.com; Slaven_Cukic@bat.com;
SAWAL Bhushan OBS/S APAC; TUPE Ashwin OBS/S APAC; 'anup.ranjan@bt.com'; 'manu.visen@bt.com'; 'brandon.ang@bt.com'; GOYAL Lavish OBS/CSO; SHARMA Narender OBS/CSO; HELMY Mostafa OBS/CSO; SHEIHA Ahmed OBS/CSO; DAHSHAN Mahmoud OBS/CSO; MOHSEN Tamer OBS/CSO; ABD
EL MEGID Rami OBS/CSO; SINGH Atul Ext OBS/CSO; OJHA Sandeep OBS/CSO; JOSHI Sandhya OBS/CSO; ELDEMALLAWY Ahmed OBS/S EUR; GOPAKUMAR Sukesh OBS/S APAC; coemeraki_bat_build@list2.orange.com;
ZZZ BAT DCSC; KUMAR Tarun K OBS/CSO; GARG Tushar OBS/CSO; THAKUR Divya OBS/CSO; ATTIA Amir OBS/CSO; HASSAN Dina H OBS/CSO; DL OCWS NOC IEC MERAKI; parau@cns com.com; cvasile@cns com.com;
ZZZ SHARED TM COE DEL; GUPTA Dipak OBS/CSO; tsc.ggn@list2.orange.com; ZZZ BAT Service Support OGSI; 'bat.support.ogsi@list2.orange.com'; FARAG Youssef OBS/CSO; BASHA Andrew OBS/CSO;
HELMY Eslam OBS/CSO; ZZZ ECS CTS2_Video
Subject: Fw:BAT Migration of ROBC01 (Romania Bucharest Business Park Category 2 /Option 5) CH4429354 >>>>>>>> Planned for 22nd Aug, 6:00 AM GMT
When: Saturday, August 22, 2020 08:00 17:00 (UTC pplluuss 02:00) Cairo.
Where: webex
Hello EMEA, 
Thanks to send this invitation to the one who handle the installation day 
Best regards, 
Andrew Akram 
01222782752 
Original message 
From: KAMEL Heba OBS/CSO <heba.kamel@orange.com>
Date: Wed, Aug 19, 2020, 4:23 PM
To: Dorio_Popenta@bat.com, "ADRIAN NEACSA (Adrian_Neacsa@bat.com)" <Adrian_Neacsa@bat.com>,
gary_clements@bat.com, Srdjan_Jeisel@bat.com, Slaven_Cukic@bat.com,
SAWAL Bhushan OBS/S APAC <bhushan.sawal@orange.com>, TUPE Ashwin OBS/S APAC <ashwin.tupe@orange.com>,
"'anup.ranjan@bt.com'" <anup.ranjan@bt.com>, "'manu.visen@bt.com'" <manu.visen@bt.com>, "'brandon.ang@bt.com'" <brandon.ang@bt.com>,
GOYAL Lavish OBS/CSO <lavish.goyal@orange.com>, SHARMA Narender OBS/CSO <narender.sharma@orange.com>,
HELMY Mostafa OBS/CSO <mostafa.helmy@orange.com>, SHEIHA Ahmed OBS/CSO <ahmed.sheiha@orange.com>, DAHSHAN
Mahmoud OBS/CSO <mahmoud.dahshan@orange.com>, MOHSEN Tamer OBS/CSO <tamer.mohsen@orange.com>, ABD
EL MEGID Rami OBS/CSO <rami.abdelmegid@orange.com>, SINGH Atul Ext OBS/CSO <atulk.singh.ext@orange.com>,
OJHA Sandeep OBS/CSO <sandeep.ojha@orange.com>, JOSHI Sandhya OBS/CSO <sandhya.joshi@orange.com>, ELDEMALLAWY
Ahmed OBS/S EUR <ahmed.eldemallawy@orange.com>, GOPAKUMAR Sukesh OBS/S APAC <sukesh.gopakumar@orange.com>,
coemeraki_bat_build@list2.orange.com, ZZZ BAT DCSC <bat.dcsc@orange.com>, KUMAR Tarun K OBS/CSO
<tarunk.kumar@orange.com>, GARG Tushar OBS/CSO <tushar.garg@orange.com>, THAKUR Divya OBS/CSO <divya.thakur@orange.com>,
ATTIA Amir OBS/CSO <amir.attia@orange.com>, HASSAN Dina H OBS/CSO <dina.h.hassan@orange.com>, DL OCWS NOC
IEC MERAKI <ocws noc.iec meraki@orange.com>, parau@cns com.com, cvasile@cns com.com,
ZZZ SHARED TM COE DEL <sharedtm.coedel@orange.com>, GUPTA Dipak OBS/CSO <dipak.gupta@orange.com>, tsc.ggn@list2.orange.com,
ZZZ BAT Service Support OGSI <bat.servicesupportogsi@orange.com>, "'bat.support.ogsi@list2.orange.com'" <bat.support.ogsi@list2.orange.com>,
ZZZ ECS VPI EMEA Demands <vpi.emea.demands@orange.com>, FARAG Youssef OBS/CSO <youssef.hamed@orange.com>,
BASHA Andrew OBS/CSO <andrew.basha@orange.com>, HELMY Eslam OBS/CSO <eslam.helmy@orange.com>, ZZZ ECS
CTS2_Video <cts2_video@orange.com>
Subject: BAT Migration of ROBC01 (Romania Bucharest Business Park Category 2 /Option 5) CH4429354 >>>>>>>> Planned for 22nd Aug, 6:00 AM GMT
Hello All,
Thanks to book that slot in your calendar for the Migration of ROBC01 (Romania Bucharest Business Park Category 2 /Option 5) CH4429354 >>> Planned for 22nd
Aug, 6:00 AM GMT
Attached the MP for your reference :
Kit List 
device name Device Role Device
IP address chassis type Serial Number Building 
Floor Room Rack 
Rack Unit power plug format 
PBUH1487 MPLS Router 10.252.67.115 
ISR4331 NA Building B 
3rd server room Rack 5 you 17 
EU 
PBUH1486 Internet Router 10.252.67.116 
ISR4431 NA Building B 
3rd server room Rack 5 you 18 
EU 
ROBC01MX01 WAN Edge/Core Device 10.252.67.113 
MX250 HW NA Building B 
3rd server room Rack 5 you 19 
EU 
ROBC01MX02 WAN Edge/Core Device 10.252.67.114 
MX250 HW NA Building B 
3rd server room Rack 5 you 20 
EU 
ROBC01SH01 Riverbed 10.253.73.36 
CXA 03070 B110 NA Building B 
3rd server room Rack 5 you 21 
EU 
OBS Resources :
OBS FE : Robert Ciobanu 0040757.053.205 email: ionut.gheorghe@radcom.roOCWS : ParisOBS UDD : Dhananjay Dass OBS VPO : Ali ZeerakOBS ISE : N/AOBS SOC : 2007Z75534TP : tbcRIVERBED : Andrew BashaGSI : Ashwin / Bhushan
Thanks & Rgds
Heba KAMEL 
Project Manager
Do not delete or change any of the following text. 
Join Webex Meeting 
Meeting number (access code): 128 288 1912 Meeting password:
vGxayEWe398 
Join from a video system or application
Dial 1282881912@orangedemo.webex.com 
You can also dial 62.109.219.4 and enter your meeting number. 
Tap to join from a mobile device (attendees only) 
 pplluuss 1 929 270 4098,,1282881912## US
Toll 
 pplluuss 33 1 85 14 85 49,,1282881912## France
Paris Toll 
Join by phone 
 pplluuss 1 929 270 4098 US Toll 
 pplluuss 33 1 85 14 85 49 France Paris Toll 
Global call in numbers | Toll free
calling restrictions 
For Attendees in China, Please Call XXXX XXXX XXXXX cannot join the meeting?
If you are a host, click
here to view host information. IMPORTANT NOTICE:
Please note that this Webex service allows audio and other information sent during the session to be recorded, which may be discoverable in a legal matter. By joining this session, you automatically consent to such recordings. If you do not consent to being
recorded, discuss your concerns with the host or do not join the session. 
<< File: BAT LAN WAN LLD ROBC01v1.9.xls >> 

                """, add_signature_regex=[

                    ]
                ).parse_text()
    print("GET_SALUTATION: ", obj.get_salutation())
    print("GET_BODY: ", obj.get_body())
    print("GET_SIGNATURE: ", obj.get_signature())
    # print("GET_TRAILING_EMAILS_ENTIRE_TEXT: ", obj.get_trailing_emails_entire_text())
