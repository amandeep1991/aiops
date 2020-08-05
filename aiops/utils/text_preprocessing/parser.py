import re


class Email:
    """
        whole_email_body: is the email content (whole body - including salutation/signature/email track etc). It must be lower-case
    """

    # Aman may do in future: Convert this utils into static utils and these parameters needs to be passed to parse_text static factory method only
    def __init__(self, whole_email_body, content_type="text") -> None:
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
            if self._body_without_signature is not None and signature.strip() == self._body_without_signature is None:
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
        r"thanks?",
        r"thanks *a[ \-\s_:\)\(\]\[]*(lot|ton)",
        r"a* *thank[ \-\s_:\)\(\]\[]+you"
        r"a*[ \-\s_:\)\(\]\[]*good[ \-\s_:\)\(\]\[]+morning",
        r"a*[ \-\s_:\)\(\]\[]*good[ \-\s_:\)\(\]\[]+afternoon",
        r"a*[ \-\s_:\)\(\]\[]*good[ \-\s_:\)\(\]\[]+evening",
        r"greetings",
        r"okay,? ?thanks?-?y?o?u?",
    ]

    signature_regex = [
        "warms? *regards?",
        "kinds? *regards?",
        "bests? *regards?",
        "many thanks",
        "thank[ -]?you",
        "talk[ -]?soo?n?",
        "yours *truly",
        "thanki?n?g? you",
        "sent from my iphone",
        "rgds?[^ing]"
        "ciao",
        "[ -]?thanks?",
        "with ?t?h?e? ?h?i?g?h?e?s?t? ?regards?",
        "regards?[^ing]",
        "cheers",
        "cordially",
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

Hello Wai,
We are still waiting for the part return under RMA 800762161.
Please confirm when can that be initiated.
Thanks & Regards,
Prashant Gupta
Senior Specialist
Customized Service Desk for GSK
Service Operations
CVS : 7357 2240 | UK:
 pplluuss 44 2073470177, US:  pplluuss 1866 325 7078 | Pin: 341030
prashantg.gupta@orange.com
Equant Tower B 8th Floor DLF
Infinity Tower Phase II 
DLF Cybercity Sector 25 Gurgaon 122002 India
www.orange business.com
From:
ZZZ ECS GSK DCSC Delhi [mailto:gsk.dcsc.delhi@orange.com] 
Sent: Monday, March 16, 2020 18:32
To: Wai To
Cc: MALIK Himanshu OBS/CSO; GUPTA Ankur OBS/CSO; gsk.dcsc.seniorspecialist@list2.orange.com;
gsk.dcsc.seniorspecialist@list2.orange.com; SHARMA Himanshu OBS/CSO; ZZZ ECS GSK DCSC Delhi
Subject: [gsk.dcsc.seniorspecialist] RE: Member switch 2 of stack PHLNDCANYD4S1 is
faulty || UKIM20010718399 || 2002N62950
Hello Wai,
Please confirm if the part has been returned to Cisco?
Regards
Swati Chaurasia 
Service Desk Specialist 
Orange Business Services
TEL  pplluuss 44
207 347 0177 ,  pplluuss 1 866 325 7078 Pin : 341030
CVS 7358 5612
Tower A | 8th Floor |DLF Infinity Tower| Phase II 
Cyber City, Sec25 |Gurgaon |Haryana | India
www.orange business.com
From:
GUPTA Ankur OBS/CSO 
Sent: Thursday, March 12, 2020 18:51
To: Wai To
Cc: MALIK Himanshu OBS/CSO; gsk.dcsc.seniorspecialist@list2.orange.com; gsk.dcsc.seniorspecialist@list2.orange.com;
SHARMA Himanshu OBS/CSO; ZZZ ECS GSK DCSC Delhi
Subject: RE: Member switch 2 of stack PHLNDCANYD4S1 is faulty || UKIM20010718399 ||
2002N62950
Hello Wai,
Please confirm If the part has been returned.
Best Regards,
Ankur Gupta
Senior Specialist Service Operations
Email: ankur1.gupta@orange.com
( : CVS
: 7357 2237; ( : UK :  pplluuss 44 2073470177 , US:  pplluuss 1866 325
7078 Option 1 than Pin : 341030
Note: Please reply to mailbox gsk.dcsc.delhi@orange.com
www.orange business.com
From:
ZZZ ECS GSK DCSC Delhi [mailto:gsk.dcsc.delhi@orange.com] 
Sent: 21 February 2020 23:02
To: Wai To
Cc: MALIK Himanshu OBS/CSO; gsk.dcsc.seniorspecialist@list2.orange.com; gsk.dcsc.seniorspecialist@list2.orange.com;
SHARMA Himanshu OBS/CSO; ZZZ ECS GSK DCSC Delhi
Subject: [gsk.dcsc.seniorspecialist] RE: Member switch 2 of stack PHLNDCANYD4S1 is
faulty || UKIM20010718399 || 2002N62950
Hello Wai,
The switch has been replaced successfully under OA# UKIM20010718399.
AP's and camera are shifted back to original ports. All the services are up and confirmed fine. Hence we will be proceeding with the closure
of the RTPA and subjected case i.e. UKIM20010718399.
As it was mentioned by you that the old switch is still in rack and cannot be removed due to one out of four screw stuck in. Also this cannot be
done next week as you are unavailable and will be back on March 02, 2020.
Once this this switch gets removed from the rack on or after March 02, 2020 we will help you with the scheduling and pick up on return RMA.
To follow up ahead on this case I have raised a new case at my end i.e. 2002N62950.
Thanks & Regards,
Prashant Gupta
Senior Specialist
Customized Service Desk for GSK
Service Operations
CVS : 7357 2240 | UK:
 pplluuss 44 2073470177, US:  pplluuss 1866 325 7078 | Pin: 341030
prashantg.gupta@orange.com
Equant Tower B 8th Floor DLF
Infinity Tower Phase II 
DLF Cybercity Sector 25 Gurgaon 122002 India
www.orange business.com
From:
Wai To [mailto:wai.x.to@gsk.com] 
Sent: Friday, February 21, 2020 20:03
To: ZZZ ECS GSK DCSC Delhi
Cc: MALIK Himanshu OBS/CSO; gsk.dcsc.seniorspecialist@list2.orange.com; gsk.dcsc.seniorspecialist@list2.orange.com;
SHARMA Himanshu OBS/CSO
Subject: RE: Member switch 2 of stack PHLNDCANYD4S1 is faulty || UKIM20010718399
Thanks Prashant, 
I will arrange his access to Navy Yard building.
Regards,
Wai
From: gsk.dcsc.delhi@orange.com <gsk.dcsc.delhi@orange.com> 
Sent: Friday, February 21, 2020 2:56 PM
To: Wai To <wai.x.to@gsk.com>
Cc: MALIK Himanshu OBS/CSO <himanshu.mallik@orange.com>; gsk.dcsc.seniorspecialist@list2.orange.com; gsk.dcsc.seniorspecialist@list2.orange.com; SHARMA Himanshu OBS/CSO <himanshu.sharma@orange.com>; ZZZ ECS GSK DCSC Delhi <gsk.dcsc.delhi@orange.com>
Subject: RE: Member switch 2 of stack PHLNDCANYD4S1 is faulty || UKIM20010718399
EXTERNAL
Hello Wai,
As discussed with you RMA has reached the site and OBS field engineer visit should be scheduled at 04:00 PM EST today.
Hence same has been done. Below are the details.
FE Name
Louis Esposito
Contact Number
 pplluuss  1 267 973 8987 
Please arrange access for the field engineer.
Thanks & Regards,
Prashant Gupta
Senior Specialist
Customized Service Desk for GSK
Service Operations
CVS : 7357 2240 | UK:
 pplluuss 44 2073470177, US:  pplluuss 1866 325 7078 | Pin: 341030
prashantg.gupta@orange.com
Equant Tower B 8th Floor DLF
Infinity Tower Phase II 
DLF Cybercity Sector 25 Gurgaon 122002 India
www.orange business.com
From:
ZZZ ECS GSK DCSC Delhi 
Sent: Friday, February 21, 2020 01:24
To: Wai To
Cc: MALIK Himanshu OBS/CSO; gsk.dcsc.seniorspecialist@list2.orange.com;
gsk.dcsc.seniorspecialist@list2.orange.com;
ZZZ ECS GSK DCSC Delhi; SHARMA Himanshu OBS/CSO
Subject: RE: Member switch 2 of stack PHLNDCANYD4S1 is faulty || UKIM20010718399
Hello Wai,
We got update from Cisco that the part will be delivered by Fri 2/21/2020 by 3:00 pm EST. 
Once the part delivered at site, we will be proceeding with the field engineer arrangement.
Thanks & Regards,
Prashant Gupta
Senior Specialist
Customized Service Desk for GSK
Service Operations
CVS : 7357 2240 | UK:
 pplluuss 44 2073470177, US:  pplluuss 1866 325 7078 | Pin: 341030
prashantg.gupta@orange.com
Equant Tower B 8th Floor DLF
Infinity Tower Phase II 
DLF Cybercity Sector 25 Gurgaon 122002 India
www.orange business.com
From:
Wai To [mailto:wai.x.to@gsk.com] 
Sent: Thursday, February 20, 2020 20:28
To: SHARMA Himanshu OBS/CSO
Cc: MALIK Himanshu OBS/CSO; gsk.dcsc.seniorspecialist@list2.orange.com;
gsk.dcsc.seniorspecialist@list2.orange.com;
ZZZ ECS GSK DCSC Delhi
Subject: RE: Member switch 2 of stack PHLNDCANYD4S1 is faulty || UKIM20010718399
Hello Himanshu,
I am shortening the email distro list for this coordination.
The switch have not been delivered yet and the shipping department is closing soon. Can we schedule the FE to arrive tomorrow at 10AM for the installation?
Regards,
Wai
From: himanshu.sharma@orange.com <himanshu.sharma@orange.com>
Sent: Thursday, February 20, 2020 9:29 AM
To: Wai To <wai.x.to@gsk.com>
Cc: MALIK Himanshu OBS/CSO <himanshu.mallik@orange.com>; gsk.dcsc.seniorspecialist@list2.orange.com; GCC Major Incident Resolution <GCC.Major Incident Resolution@gsk.com>;
Ww Internationalhub <ww.internationalhub@gsk.com>; gsk.dcsc.seniorspecialist@list2.orange.com; ZZZ ECS GSK DCSC Delhi <gsk.dcsc.delhi@orange.com>
Subject: RE: Member switch 2 of stack PHLNDCANYD4S1 is faulty || UKIM20010718399
Importance: High
EXTERNAL
Hello Wai,
We would like to update that below is the Part ETA received from Cisco. 
Request you to please confirm once received.
Estimated Arrival:
02/20/2020 05:00 PM(GMT 5)
Carrier:
FEDEX
390519299455 
Regards
Himanshu Sharma
Incident Manager
Himanshu.sharma@orange.com 
CVS : 7357 3018 UK:
 pplluuss 44 2073470177, US: pplluuss 1866 325 7078 | Pin:
341030
Orange. Infinity Tower, DLF Cyber City, Gurgaon, India 
http://www.orange business.com
From:
ZZZ ECS GSK DCSC Delhi 
Sent: Wednesday, February 19, 2020 23:47
To: Wai To
Cc: MALIK Himanshu OBS/CSO; gsk.dcsc.seniorspecialist@list2.orange.com;
GCC.Major Incident Resolution@gsk.com;
Ww Internationalhub; SHARMA Himanshu OBS/CSO; gsk.dcsc.seniorspecialist@list2.orange.com;
ZZZ ECS GSK DCSC Delhi
Subject: Member switch 2 of stack PHLNDCANYD4S1 is faulty || UKIM20010718399
 pplluuss  pplluuss  pplluuss  Updating Subject Line  pplluuss  pplluuss  pplluuss 
Hello Wai,
Thanks for your help in moving the camera and access points to working interfaces. Now they are working as expected.
Below are the devices and actions for their interfaces. These devices were moved under OA# CRQ000000794978.
Device
Actual Interface
Moved to Interface
Current Status
Camera
Gi2/0/13
Gi1/0/4
Interface is Up
phlndwlnydap4s05
Gi2/0/24
Gi1/0/1
AP is Up and associated to the Controller
phlndwlnydap4s19
Gi2/0/23
Gi1/0/2
AP is Up and associated to the Controller
phlndwlnydap4s35
Gi2/0/22
Gi1/0/3
AP is Up and associated to the Controller
As per discussion, there is no more impact and users who were using the wired LAN connections will be moving on wireless network until the switch
gets replaced. Moreover the RTPA can be downgraded to Yellow.
RMA status 
Faulty device is holding the 8X5XNBD contract. RMA ETA is still awaited from Cisco. 
Thanks & Regards,
Prashant Gupta
Senior Specialist
Customized Service Desk for GSK
Service Operations
CVS : 7357 2240 | UK:
 pplluuss 44 2073470177, US:  pplluuss 1866 325 7078 | Pin: 341030
prashantg.gupta@orange.com
Equant Tower B 8th Floor DLF
Infinity Tower Phase II 
DLF Cybercity Sector 25 Gurgaon 122002 India
www.orange business.com
From:
SHARMA Himanshu OBS/CSO [mailto:himanshu.sharma@orange.com]
Sent: Wednesday, February 19, 2020 21:03
To: Wai To; GCC.Major Incident Resolution@gsk.com;
Ww Internationalhub
Cc: MALIK Himanshu OBS/CSO; gsk.dcsc.seniorspecialist@list2.orange.com
Subject: [gsk.dcsc.seniorspecialist] RE: RE : WIRELESS APs DISASSOCIATED FROM CONTROLLER
|| UKIM20010718399
Importance: High
Hello All,
An Orange RTPA has been raised moreover TAC case with cisco for your reference is 688487485.
We will share Part ETA soon and accordingly align Field Tech at site.
Regards
Himanshu Sharma
Incident Manager
Himanshu.sharma@orange.com 
CVS : 7357 3018 UK:
 pplluuss 44 2073470177, US: pplluuss 1866 325 7078 | Pin:
341030
Orange. Infinity Tower, DLF Cyber City, Gurgaon, India 
http://www.orange business.com
From:
SHARMA Himanshu OBS/CSO 
Sent: Wednesday, February 19, 2020 20:31
To: Wai To; GCC.Major Incident Resolution@gsk.com;
Ww Internationalhub
Cc: ZZZ ECS GSK DCSC Delhi; MALIK Himanshu OBS/CSO
Subject: RE: RE : WIRELESS APs DISASSOCIATED FROM CONTROLLER || UKIM20010718399
Importance: High
Hello Wai,
As discussed, since the member is showing removed in stack and therefore we are not able to check further.
No User impact as they will be using the nearby APs for connectivity however we are raising an Orange RTPA since 3 AP's and LAN connection are
still down.
We are raising RMA now and will share ETA soon.
Hello GCC IR,
Please this is for your information.
Regards
Himanshu Sharma
Incident Manager
Himanshu.sharma@orange.com 
CVS : 7357 3018 UK:
 pplluuss 44 2073470177, US: pplluuss 1866 325 7078 | Pin:
341030
Orange. Infinity Tower, DLF Cyber City, Gurgaon, India 
http://www.orange business.com
From:
Wai To [mailto:wai.x.to@gsk.com] 
Sent: Wednesday, February 19, 2020 20:13
To: SHARMA Himanshu OBS/CSO
Cc: ZZZ ECS GSK DCSC Delhi
Subject: RE: RE : WIRELESS APs DISASSOCIATED FROM CONTROLLER || USIM10018723452||USIM10018723458||USIM10018723464
Hi Himanshu,
The whole logical switch is NOT down and it is just one of the switch members had a power supply and switch issue. The three connected APs and LAN connections are
disrupted in that part of the building while users will be using the nearby APs for connectivity.
From the switch configuration, did you see any other critical types of connection base on the interface description on this particular stack?
Regards,
Wai
From: himanshu.sharma@orange.com <himanshu.sharma@orange.com>
Sent: Wednesday, February 19, 2020 3:05 PM
To: Wai To <wai.x.to@gsk.com>
Cc: ZZZ ECS GSK DCSC Delhi <gsk.dcsc.delhi@orange.com>
Subject: RE: RE : WIRELESS APs DISASSOCIATED FROM CONTROLLER || USIM10018723452||USIM10018723458||USIM10018723464
Importance: High
EXTERNAL
Hello Wai,
Please can you also confirm the current impact so that an appropriate RTPA can be raised.
Regards
Himanshu Sharma
Incident Manager
Himanshu.sharma@orange.com 
CVS : 7357 3018 UK:
 pplluuss 44 2073470177, US: pplluuss 1866 325 7078 | Pin:
341030
Orange. Infinity Tower, DLF Cyber City, Gurgaon, India 
http://www.orange business.com
From:
Wai To [mailto:wai.x.to@gsk.com] 
Sent: Wednesday, February 19, 2020 20:00
To: ZZZ ECS GSK DCSC Delhi
Subject: RE: RE : WIRELESS APs DISASSOCIATED FROM CONTROLLER || USIM10018723452||USIM10018723458||USIM10018723464
Hi Nishtha,
Ed and I just went to check on the switch. Switch stack#2 is down in phlndcanyd4s1 and will not boot up. Please request an RMA
and a FE here to replace this switch.
Regards,
Wai
From: gsk.dcsc.delhi@orange.com <gsk.dcsc.delhi@orange.com> 
Sent: Wednesday, February 19, 2020 2:25 PM
To: Wai To <wai.x.to@gsk.com>
Cc: ZZZ ECS GSK DCSC Delhi <gsk.dcsc.delhi@orange.com>
Subject: RE : WIRELESS APs DISASSOCIATED FROM CONTROLLER || USIM10018723452||USIM10018723458||USIM10018723464
EXTERNAL
Hi Wai,
With reference to the subjected case, following Aps (which are listed below) and their respective switch interfaces to which they are connected are down and in not
connected state. Kindly get the physical checks done for mentioned APs and update us post checks.
AP Name
Switch
Neighbor Port
PHLNDWLNYDAP4S05
phlndcanyd4s1
GigabitEthernet2/0/24
PHLNDWLNYDAP4S19
phlndcanyd4s1
GigabitEthernet2/0/23
PHLNDWLNYDAP4S35
phlndcanyd4s1
GigabitEthernet2/0/22
Regards
Nishtha Rai | Service Operations
Orange Business Services
TEL  pplluuss 44
207 347 0177 ,  pplluuss 1 866 325 7078 Pin : 341030
CVS 7358 5612
Tower B | 8th Floor |DLF Infinity Tower| Phase II 
Cyber City, Sec25 |Gurgaon |Haryana | India
_________________________________________________________________________________________________________________________
Ce message et ses pieces jointes peuvent contenir des informations confidentielles ou privilegiees et ne doivent donc
pas etre diffuses, exploites ou copies sans autorisation. Si vous avez recu ce message par erreur, veuillez le signaler
a l'expediteur et le detruire ainsi que les pieces jointes. Les messages electroniques etant susceptibles d'alteration,
Orange decline toute responsabilite si ce message a ete altere, deforme ou falsifie. Merci.
This message and its attachments may contain confidential or privileged information that may be protected by law;
they should not be distributed, used or copied without authorisation.
If you have received this email in error, please notify the sender and delete this message and its attachments.
As emails may be altered, Orange is not liable for messages that have been modified, changed or falsified.
Thank you.
GSK monitors email communications sent to and from GSK in order to protect GSK, our employees, customers,
suppliers and business partners, from cyber threats and loss of GSK Information. GSK monitoring is conducted with appropriate confidentiality controls and in accordance with local laws and after appropriate consultation.
_________________________________________________________________________________________________________________________
Ce message et ses pieces jointes peuvent contenir des informations confidentielles ou privilegiees et ne doivent donc
pas etre diffuses, exploites ou copies sans autorisation. Si vous avez recu ce message par erreur, veuillez le signaler
a l'expediteur et le detruire ainsi que les pieces jointes. Les messages electroniques etant susceptibles d'alteration,
Orange decline toute responsabilite si ce message a ete altere, deforme ou falsifie. Merci.
This message and its attachments may contain confidential or privileged information that may be protected by law;
they should not be distributed, used or copied without authorisation.
If you have received this email in error, please notify the sender and delete this message and its attachments.
As emails may be altered, Orange is not liable for messages that have been modified, changed or falsified.
Thank you.
GSK monitors email communications sent to and from GSK in order to protect GSK, our employees, customers, suppliers and business partners,
from cyber threats and loss of GSK Information. GSK monitoring is conducted with appropriate confidentiality controls and in accordance with local laws and after appropriate consultation.
_________________________________________________________________________________________________________________________
Ce message et ses pieces jointes peuvent contenir des informations confidentielles ou privilegiees et ne doivent donc
pas etre diffuses, exploites ou copies sans autorisation. Si vous avez recu ce message par erreur, veuillez le signaler
a l'expediteur et le detruire ainsi que les pieces jointes. Les messages electroniques etant susceptibles d'alteration,
Orange decline toute responsabilite si ce message a ete altere, deforme ou falsifie. Merci.
This message and its attachments may contain confidential or privileged information that may be protected by law;
they should not be distributed, used or copied without authorisation.
If you have received this email in error, please notify the sender and delete this message and its attachments.
As emails may be altered, Orange is not liable for messages that have been modified, changed or falsified.
Thank you.
GSK monitors email communications sent to and from GSK in order to protect GSK, our employees, customers, suppliers and business partners,
from cyber threats and loss of GSK Information. GSK monitoring is conducted with appropriate confidentiality controls and in accordance with local laws and after appropriate consultation.
_________________________________________________________________________________________________________________________
Ce message et ses pieces jointes peuvent contenir des informations confidentielles ou privilegiees et ne doivent donc
pas etre diffuses, exploites ou copies sans autorisation. Si vous avez recu ce message par erreur, veuillez le signaler
a l'expediteur et le detruire ainsi que les pieces jointes. Les messages electroniques etant susceptibles d'alteration,
Orange decline toute responsabilite si ce message a ete altere, deforme ou falsifie. Merci.
This message and its attachments may contain confidential or privileged information that may be protected by law;
they should not be distributed, used or copied without authorisation.
If you have received this email in error, please notify the sender and delete this message and its attachments.
As emails may be altered, Orange is not liable for messages that have been modified, changed or falsified.
Thank you.
GSK monitors email communications sent to and from GSK in order to protect GSK, our employees, customers, suppliers and business partners,
from cyber threats and loss of GSK Information. GSK monitoring is conducted with appropriate confidentiality controls and in accordance with local laws and after appropriate consultation.

    """).parse_text()
    print("GET_SALUTATION: ", obj.get_salutation())
    print("GET_BODY: ", obj.get_body())
    print("GET_SIGNATURE: ", obj.get_signature())
    print("GET_TRAILING_EMAILS_ENTIRE_TEXT: ", obj.get_trailing_emails_entire_text())
