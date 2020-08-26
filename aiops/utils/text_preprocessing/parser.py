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
        "warms? *regards?",
        "kinds? *regards?",
        "bests? *regards?",
        "many thanks",
        "thank[ -]?you",
        "thanks? and regards?",
        "talk[ -]?soo?n?",
        "yours *truly",
        "thanki?n?g? you",
        "sent from my iphone",
        "rgds?[^ing]"
        "ciao",
        "(?<!([\n\s]many|great) )thanks?",
        "with ?t?h?e? ?h?i?g?h?e?s?t? ?regards?",
        "(?<!(\w and|[\n\s]with|kinds|[\n\s]kind|bests|[\n\s]best) )regards?[^ing]",
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
    obj = Email("""Hi Kavya/Nihas,The ticket is set to withdrawn, as per update on the ticket. No action needed. Thank you.Please let us know if your preferred language is French and we will engage our translation services team.Veuillez nous aviser si vous souhaitez un service en franais, nous ferons appel aux services d'une quipe de traduction.Thanks and Regards,Anoop C P Global Network OperationsGlobal Business Services, IS&T Operations Rio TintoAccenture India Delivery Centre, Pritech Park SEZ, Block VII, Tower A,Bellandur, Outer Ring Road ,Varthur Hobli, Bangalore 560103 pplluuss 61 736253864 anoop.pushpangadan@riotinto.com www.riotinto.comFrom: Pushpangadan, Anoop (IST) Sent: Wednesday, August 26, 2020 3:31 PMTo: riotinto.csd.delhi@orange.com; IST Infra APAC Networks <ISTInfraAPACNetworks@riotinto.com>; Adak, Swastidyuti (IST) <Swastidyuti.Adak@riotinto.com>; Sahu, Alok K (IST) <Alok.Sahu@riotinto.com>; Sudhakaran, Abhijith (IST) <Abhijith.Sudhakaran@riotinto.com>;IST Infra Remote Secure Access <IST.Infra.Remote.Secure.Access@riotinto.com>; Koppishetty, Kavya (IST) <Kavya.Koppishetty@riotinto.com>; Nasibudeen, Nihas (IST) <Nihas.Nasibudeen@riotinto.com>Cc: rio.tinto.itcsm@list2.orange.com; Reddy, Sridhar (Orange via the Internet) <sridhar.reddy@orange.com>; CLUBB Steven OBS/CSO <steven.clubb@orange.com>; AHUJA Ravikant OBS/CSO <ravikant.ahuja@orange.com>; ALPHONSE Marina OBS/CSO <marina.alphonse@orange.com>;ZZZ ECS MSIO Egypt <msio.egypt@orange.com>Subject: RE: [External] BEM Alert on ssl rio_tinto rueil inet JSAVA external authentication server is unreachable || OBS ref : 2008H46759 : INC3691023Importance: High pplluuss  pplluuss  pplluuss  Remote Secure access/Security team pplluuss  pplluuss HI Kavya/NihasPlease check the Auth server SymantecVIP RioTinto MEL reported by OBS team. Please check and confirm back as soon as possible.Please let us know if your preferred language is French and we will engage our translation services team.Veuillez nous aviser si vous souhaitez un service en franais, nous ferons appel aux services d'une quipe de traduction.Thanks and Regards,Anoop C P Global Network OperationsGlobal Business Services, IS&T Operations Rio TintoAccenture India Delivery Centre, Pritech Park SEZ, Block VII, Tower A,Bellandur, Outer Ring Road ,Varthur Hobli, Bangalore 560103 pplluuss 61 736253864 anoop.pushpangadan@riotinto.com www.riotinto.comFrom: riotinto.csd.delhi@orange.com [mailto:riotinto.csd.delhi@orange.com]Sent: Wednesday, August 26, 2020 3:05 PMTo: IST Infra APAC Networks <ISTInfraAPACNetworks@riotinto.com>; Adak, Swastidyuti (IST) <Swastidyuti.Adak@riotinto.com>; Sahu, Alok K (IST) <Alok.Sahu@riotinto.com>;Pushpangadan, Anoop (IST) <Anoop.Pushpangadan@riotinto.com>; Sudhakaran, Abhijith (IST) <Abhijith.Sudhakaran@riotinto.com>Cc: ZZZ ECS Riotinto CSD Delhi <riotinto.csd.delhi@orange.com>;rio.tinto.itcsm@list2.orange.com; Reddy, Sridhar (Orange via the Internet) <sridhar.reddy@orange.com>; CLUBB Steven OBS/CSO <steven.clubb@orange.com>;AHUJA Ravikant OBS/CSO <ravikant.ahuja@orange.com>; ALPHONSE Marina OBS/CSO <marina.alphonse@orange.com>; ZZZ ECS MSIO Egypt <msio.egypt@orange.com>Subject: [External] BEM Alert on ssl rio_tinto rueil inet JSAVA external authentication server is unreachable || OBS ref : 2008H46759Hello Accenture team,We have received proactive ticket for SSL device : SSL RIO_TINTO RUEIL INET for Rueil SNIG.So we have engaged our L2 team to investigate the issue further.Our L2 team check and found that, authentication server SymantecVIP RioTinto MEL is down .Request to you, please check with your internal team and advise us urgently, as this server is managed by your team.Note : Rueil SNIG soft disconnected today at 6 AM AWAS. Please check and confirm if server also disconnected?Thanks and Regards,Pritesh KumarIncident Manager Rio TintoService Operations, India Major Service Centerpritesh.kumar@orange.comToll free:  pplluuss 18663257078 PIN341011# ||CVS (() 7357 6027riotinto.csd.delhi@orange.comwww.orange business.comTry our new chat interface for update on existing incidents. Reach us by initiating a chat withrio.tinto.service.desk@orange.comin your chat application !!Go Green, Save Paper_________________________________________________________________________________________________________________________Ce message et ses pieces jointes peuvent contenir des informations confidentielles ou privilegiees et ne doivent doncpas etre diffuses, exploites ou copies sans autorisation. Si vous avez recu ce message par erreur, veuillez le signalera l'expediteur et le detruire ainsi que les pieces jointes. Les messages electroniques etant susceptibles d'alteration,Orange decline toute responsabilite si ce message a ete altere, deforme ou falsifie. Merci.This message and its attachments may contain confidential or privileged information that may be protected by law;they should not be distributed, used or copied without authorisation.If you have received this email in error, please notify the sender and delete this message and its attachments.As emails may be altered, Orange is not liable for messages that have been modified, changed or falsified.Thank you.""", add_signature_regex=['Ravikant Ahuja[\\s\\.\\n]*Manager -? ?Service Operations']).parse_text()
    print("GET_SALUTATION: ", obj.get_salutation())
    print("GET_BODY: ", obj.get_body())
    print("GET_SIGNATURE: ", obj.get_signature())
    print("GET_TRAILING_EMAILS_ENTIRE_TEXT: ", obj.get_trailing_emails_entire_text())
