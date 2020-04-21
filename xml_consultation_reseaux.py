# -*- coding:utf-8 -*-
"""
/***************************************************************************
 xml_consultation_reseau.py

 DT-DICT-DC-ATU xml parsing class

 XmlConsultationReseau class extracts data from DT-DICT-DC-ATU xml file and
 put them in dictionary.

        begin                : 2020-03-07
        git sha              : $Format:%H$
        copyright            : (C) 2020 by Jean-Marie Arsac
        email                : jmarsac@azimut.fr
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from lxml import etree


class XmlConsultationReseaux:
    def __init__(self):
        """Constructor"""
        self.__type_demande = ""
        self.__no_teleservice = ""
        self.__dictionnaire = {}
        self.__srs_name = ""
        self.__epsg = ""
        self.__srs_dimension = ""
        self.__gml_geom = []

    def open(self, filename):
        parser = etree.XMLParser(remove_blank_text=True)
        self.__doc = etree.parse(filename, parser)
        self.__root = self.__doc.getroot()
        self.__ineris_prefix = ""
        self.__insee_prefix = ""
        self.__gml_prefix = ""
        self.__xlink_prefix = ""
        self.__gmd_prefix = ""
        self.__gco_prefix = ""
        self.__gsr_prefix = ""
        self.__gts_prefix = ""
        self.__gss_prefix = ""
        self.__nsmap = self.__root.nsmap.copy()

        # fix None key value
        i = 1
        ki = 'p'
        for k in self.__nsmap.keys():
            if k is None:
                self.__nsmap[ki + str(i)] = self.__nsmap.pop(k)
                i += 1

        for k in self.__nsmap.keys():
            if k is not None:
                if "http://www.reseaux-et-canalisations.gouv.fr/schema-teleservice/" in self.__nsmap[k]:
                    self.__ineris_prefix = k + ":"
                elif "http://xml.insee.fr/schema" in self.__nsmap[k]:
                    self.__insee_prefix = k + ":"
                elif "http://www.opengis.net/gml/" in self.__nsmap[k]:
                    self.__gml_prefix = k + ":"
                elif "http://www.w3.org/1999/xlink" in self.__nsmap[k]:
                    self.__xlink_prefix = k + ":"
                elif "http://www.isotc211.org/2005/gmd" in self.__nsmap[k]:
                    self.__gmd_prefix = k + ":"
                elif "http://www.isotc211.org/2005/gco" in self.__nsmap[k]:
                    self.__gco_prefix = k + ":"
                elif "http://www.isotc211.org/2005/gsr" in self.__nsmap[k]:
                    self.__gsr_prefix = k + ":"
                elif "http://www.isotc211.org/2005/gts" in self.__nsmap[k]:
                    self.__gts_prefix = k + ":"
                elif "http://www.isotc211.org/2005/gss" in self.__nsmap[k]:
                    self.__gss_prefix = k + ":"

        el = self.__root.xpath('/{0}dossierConsultation/{0}*'.format(self.__ineris_prefix), namespaces=self.__nsmap)

        if el is not None and len(el) > 0:
            if 'dtDictConjointes' in el[0].tag:
                self.__type_demande = 'DC'
            elif 'DT' in el[0].tag:
                self.__type_demande = 'DT'
            elif 'DICT' in el[0].tag:
                self.__type_demande = 'DICT'
            elif 'ATU' in el[0].tag:
                self.__type_demande = 'ATU'
            self.__dictionnaire["type_demande"] = self.__type_demande

            if self.__type_demande == 'DT':
                el = self.__root.xpath('/{0}dossierConsultation/{0}*/{0}noConsultationDuTeleserviceSeize'.format(self.__ineris_prefix),namespaces=self.__nsmap)
            else:
                el = self.__root.xpath('/{0}dossierConsultation/{0}*/{0}noConsultationDuTeleservice'.format(self.__ineris_prefix), namespaces=self.__nsmap)
            if el is not None and len(el) > 0:
                self.__no_teleservice = el[0].text
                self.__dictionnaire["no_teleservice"] = el[0].text
        return self.__type_demande

    def __extract_emprise_srs_name(self):
        el = self.__root.xpath('/descendant::{0}emprise/{0}geometrie'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__srs_name = el[0].get("srsName")
            self.__epsg = self.__srs_name[self.__srs_name.rfind(":") + 1:]

    def __extract_emprise_srs_dimension(self):
        el = self.__root.xpath('/descendant::{0}emprise/{0}geometrie'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__srs_dimension = el[0].get("srsDimension")

    def __extract_emprise_geom(self):
        el = self.__root.xpath('/descendant::{0}emprise/{0}geometrie/{1}surfaceMembers/*'.format(self.__ineris_prefix,self.__gml_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            for e in el:
                self.__gml_geom.append(etree.tounicode(e))

    def view_emprise_gml_geom(self):
        for gg in self.__gml_geom:
            print(gg)

    def emprise_gml_geom(self):
        return self.__gml_geom

    def emprise_epsg(self):
        return self.__epsg

    def emprise_dimension(self):
        return self.__srs_dimension

    def extract_data(self):
        if self.__type_demande == "DT":
            self.__fill_dictionaire_dt()
        elif self.__type_demande == "DICT":
            self.__fill_dictionaire_dict()
        elif self.__type_demande == "DC":
            self.__fill_dictionaire_dc()
        elif self.__type_demande == "ATU":
            self.__fill_dictionaire_atu()

        if self.__type_demande in ["DT", "DICT", "DC", "ATU"]:
            self.__extract_emprise_srs_name()
            self.__extract_emprise_srs_dimension()
            self.__extract_emprise_geom()

        self.__dictionnaire["taille_des_plans"] = ""
        if self.__type_demande in ["DT", "DICT", "DC"]:
            el = self.__root.xpath('/descendant::{0}modeReceptionElectronique/{0}tailleDesPlans'.format(self.__ineris_prefix), namespaces=self.__nsmap)
            if el is not None and len(el) > 0:
                self.__dictionnaire["taille_des_plans"] = el[0].text
            el = self.__root.xpath('/descendant::{0}modeReceptionElectronique/{0}couleurDesPlans'.format(self.__ineris_prefix), namespaces=self.__nsmap)
            if el is not None and len(el) > 0:
                self.__dictionnaire["couleur_des_plans"] = el[0].text
            el = self.__root.xpath('/descendant::{0}modeReceptionElectronique/{0}souhaitDePlansVectoriels'.format(self.__ineris_prefix), namespaces=self.__nsmap)
            if el is not None and len(el) > 0:
                self.__dictionnaire["plans_vectoriels"] = el[0].text

    def __fill_dictionaire_dt(self):
        el = self.__root.xpath('/descendant::{0}DT/{0}noAffaireDuResponsableDuProjet'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["dec_affaire"] = el[0].text
        el = self.__root.xpath('/descendant::{0}DT/{0}dateDeLaDeclaration'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["declaration_at"] = el[0].text
        el = self.__root.xpath('/descendant::{0}DT/{0}typeEntite'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["dec_type_entite"] = el[0].text
        el = self.__root.xpath('/descendant::{0}DT/{0}emplacementDuProjet/{0}communePrincipale'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["tvx_commune"] = el[0].text
        el = self.__root.xpath('/descendant::{0}DT/{0}emplacementDuProjet/{0}codeINSEE'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["tvx_code_insee"] = el[0].text
        el = self.__root.xpath('/descendant::{0}DT/{0}emplacementDuProjet/{0}adresse'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["tvx_adresse"] = el[0].text
        el = self.__root.xpath('/descendant::{0}DT/{0}representantDuResponsableDeProjet/{0}denomination'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["dec_denomination"] = el[0].text
        el = self.__root.xpath('/descendant::{0}DT/{0}representantDuResponsableDeProjet/{0}numero'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["dec_no_voie"] = el[0].text
        el = self.__root.xpath('/descendant::{0}DT/{0}representantDuResponsableDeProjet/{0}voie'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["dec_voie"] = el[0].text
        el = self.__root.xpath('/descendant::{0}DT/{0}representantDuResponsableDeProjet/{0}lieuDitBP'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            # TODO add "BP " as prefix if digits only
            self.__dictionnaire["dec_lieudit_bp"] = el[0].text
        el = self.__root.xpath('/descendant::{0}DT/{0}representantDuResponsableDeProjet/{0}adresse2'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["dec_adresse2"] = el[0].text
        el = self.__root.xpath('/descendant::{0}DT/{0}representantDuResponsableDeProjet/{0}codePostal'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["dec_code_postal"] = el[0].text
        el = self.__root.xpath( '/descendant::{0}DT/{0}representantDuResponsableDeProjet/{0}commune'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["dec_commune"] = el[0].text
        el = self.__root.xpath('/descendant::{0}DT/{0}responsableDuProjet/{0}pays'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["dec_pays"] = el[0].text
        el = self.__root.xpath('/descendant::{0}DT/{0}representantDuResponsableDeProjet/{0}personneAcontacter'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["dec_contact"] = el[0].text
        el = self.__root.xpath( '/descendant::{0}DT/{0}representantDuResponsableDeProjet/{0}courriel'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["dec_email"] = el[0].text
        el = self.__root.xpath('/descendant::{0}DT/{0}representantDuResponsableDeProjet/{0}tel'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["dec_tel"] = el[0].text
        el = self.__root.xpath('/descendant::{0}DT/{0}representantDuResponsableDeProjet/{0}fax'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["dec_fax"] = el[0].text

    def __fill_dictionaire_dict(self):
        el = self.__root.xpath('/descendant::{0}DICT/{0}noAffaireDeLexecutantDesTravaux'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["dec_affaire"] = el[0].text
        el = self.__root.xpath('/descendant::{0}DICT/{0}dateDeLaDeclaration'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["declaration_at"] = el[0].text
        el = self.__root.xpath('/descendant::{0}DICT/{0}emplacementDesTravaux/{0}communePrincipale'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["tvx_commune"] = el[0].text
        el = self.__root.xpath('/descendant::{0}DICT/{0}emplacementDesTravaux/{0}codeINSEE'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["tvx_code_insee"] = el[0].text
        el = self.__root.xpath('/descendant::{0}DICT/{0}emplacementDesTravaux/{0}adresse'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["tvx_adresse"] = el[0].text
        el = self.__root.xpath('/descendant::{0}DICT/{0}executantDesTravaux/{0}noSiret'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["dec_siret"] = el[0].text
        el = self.__root.xpath('/descendant::{0}DICT/{0}executantDesTravaux/{0}denomination'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["dec_denomination"] = el[0].text
        el = self.__root.xpath('/descendant::{0}DICT/{0}executantDesTravaux/{0}numero'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["dec_no_voie"] = el[0].text
        el = self.__root.xpath('/descendant::{0}DICT/{0}executantDesTravaux/{0}voie'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["dec_voie"] = el[0].text
        el = self.__root.xpath('/descendant::{0}DICT/{0}executantDesTravaux/{0}lieuDitBP'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            # TODO add "BP " as prefix if digits only
            self.__dictionnaire["dec_lieudit_bp"] = el[0].text
        el = self.__root.xpath('/descendant::{0}DICT/{0}executantDesTravaux/{0}complementService'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["dec_adresse2"] = el[0].text
        el = self.__root.xpath('/descendant::{0}DICT/{0}executantDesTravaux/{0}codePostal'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["dec_code_postal"] = el[0].text
        el = self.__root.xpath('/descendant::{0}DICT/{0}executantDesTravaux/{0}commune'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["dec_commune"] = el[0].text
        el = self.__root.xpath('/descendant::{0}DICT/{0}executantDesTravaux/{0}pays'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["dec_pays"] = el[0].text
        el = self.__root.xpath('/descendant::{0}DICT/{0}executantDesTravaux/{0}nomDeLaPersonneAContacter'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["dec_contact"] = el[0].text
        el = self.__root.xpath( '/descendant::{0}DICT/{0}executantDesTravaux/{0}courriel'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["dec_email"] = el[0].text
        el = self.__root.xpath('/descendant::{0}DICT/{0}executantDesTravaux/{0}tel'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["dec_tel"] = el[0].text
        el = self.__root.xpath('/descendant::{0}DICT/{0}executantDesTravaux/{0}fax'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["dec_fax"] = el[0].text

    def __fill_dictionaire_dc(self):
        el = self.__root.xpath('/descendant::{0}partieDICT/{0}noAffaireDeLexecutantDesTravaux'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["dec_affaire"] = el[0].text
        el = self.__root.xpath('/descendant::{0}dtDictConjointes/{0}dateDeLaDeclaration'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["declaration_at"] = el[0].text
        el = self.__root.xpath('/descendant::{0}partieDT/{0}typeEntite'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["dec_type_entite"] = el[0].text
        el = self.__root.xpath('/descendant::{0}partieDICT/{0}emplacementDesTravaux/{0}communePrincipale'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["tvx_commune"] = el[0].text
        el = self.__root.xpath('/descendant::{0}partieDICT/{0}emplacementDesTravaux/{0}codeINSEE'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["tvx_code_insee"] = el[0].text
        el = self.__root.xpath('/descendant::{0}partieDICT/{0}emplacementDesTravaux/{0}adresse'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["tvx_adresse"] = el[0].text
        el = self.__root.xpath('/descendant::{0}partieDICT/{0}executantDesTravaux/{0}denomination'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["dec_denomination"] = el[0].text
        el = self.__root.xpath('/descendant::{0}partieDICT/{0}executantDesTravaux/{0}numero'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["dec_no_voie"] = el[0].text
        el = self.__root.xpath('/descendant::{0}partieDICT/{0}executantDesTravaux/{0}voie'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["dec_voie"] = el[0].text
        el = self.__root.xpath('/descendant::{0}partieDICT/{0}executantDesTravaux/{0}lieuDitBP'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            # TODO add "BP " as prefix if digits only
            self.__dictionnaire["dec_lieudit_bp"] = el[0].text
        el = self.__root.xpath('/descendant::{0}partieDICT/{0}executantDesTravaux/{0}complementService'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["dec_adresse2"] = el[0].text
        el = self.__root.xpath('/descendant::{0}partieDICT/{0}executantDesTravaux/{0}codePostal'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["dec_code_postal"] = el[0].text
        el = self.__root.xpath('/descendant::{0}partieDICT/{0}executantDesTravaux/{0}commune'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["dec_commune"] = el[0].text
        el = self.__root.xpath('/descendant::{0}partieDICT/{0}executantDesTravaux/{0}pays'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["dec_pays"] = el[0].text
        el = self.__root.xpath( '/descendant::{0}partieDICT/{0}executantDesTravaux/{0}nomDeLaPersonneAContacter'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["dec_contact"] = el[0].text
        el = self.__root.xpath('/descendant::{0}partieDICT/{0}executantDesTravaux/{0}courriel'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["dec_email"] = el[0].text
        el = self.__root.xpath('/descendant::{0}partieDICT/{0}executantDesTravaux/{0}tel'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["dec_tel"] = el[0].text
        el = self.__root.xpath('/descendant::{0}partieDICT/{0}executantDesTravaux/{0}fax'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["dec_fax"] = el[0].text

    def __fill_dictionaire_atu(self):
        el = self.__root.xpath('/descendant::{0}ATU/{0}date'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["declaration_at"] = el[0].text
        el = self.__root.xpath('/descendant::{0}ATU/{0}travauxEmplacementDureeDescription/{0}commune'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is None:
            el = self.__root.xpath('/descendant::{0}listeDesEmplacementsDesCommunesConcerneesATU/{0}emplacementDeLaCommuneConcernee/{0}nomDeLaCommune'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["tvx_commune"] = el[0].text
        el = self.__root.xpath('/descendant::{0}listeDesEmplacementsDesCommunesConcerneesATU/{0}emplacementDeLaCommuneConcernee/{0}codeINSEE'.format( self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["tvx_code_insee"] = el[0].text
        el = self.__root.xpath('/descendant::{0}ATU/{0}travauxEmplacementDureeDescription/{0}adresse'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["tvx_adresse"] = el[0].text
        el = self.__root.xpath('/descendant::{0}ATU/{0}personneOrdonnantLesTravauxUrgents/{0}nom'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["dec_denomination"] = el[0].text
        el = self.__root.xpath('/descendant::{0}ATU/{0}personneOrdonnantLesTravauxUrgents/{0}numero'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["dec_no_voie"] = el[0].text
        el = self.__root.xpath('/descendant::{0}ATU/{0}personneOrdonnantLesTravauxUrgents/{0}voie'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["dec_voie"] = el[0].text
        el = self.__root.xpath('/descendant::{0}ATU/{0}personneOrdonnantLesTravauxUrgents/{0}lieuDitBP'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            # TODO add "BP " as prefix if digits only
            self.__dictionnaire["dec_lieudit_bp"] = el[0].text
        el = self.__root.xpath('/descendant::{0}ATU/{0}personneOrdonnantLesTravauxUrgents/{0}complementService'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["dec_adresse2"] = el[0].text
        el = self.__root.xpath('/descendant::{0}ATU/{0}personneOrdonnantLesTravauxUrgents/{0}codePostal'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["dec_code_postal"] = el[0].text
        el = self.__root.xpath('/descendant::{0}ATU/{0}personneOrdonnantLesTravauxUrgents/{0}commune'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["dec_commune"] = el[0].text
        el = self.__root.xpath('/descendant::{0}ATU/{0}personneOrdonnantLesTravauxUrgents/{0}pays'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["dec_pays"] = el[0].text
        el = self.__root.xpath('/descendant::{0}ATU/{0}personneOrdonnantLesTravauxUrgents/{0}nomDeLaPersonneAContacter'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["dec_contact"] = el[0].text
        el = self.__root.xpath('/descendant::{0}ATU/{0}personneOrdonnantLesTravauxUrgents/{0}courriel'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["dec_email"] = el[0].text
        el = self.__root.xpath('/descendant::{0}ATU/{0}personneOrdonnantLesTravauxUrgents/{0}tel'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["dec_tel"] = el[0].text
        el = self.__root.xpath('/descendant::{0}ATU/{0}personneOrdonnantLesTravauxUrgents/{0}fax'.format(self.__ineris_prefix), namespaces=self.__nsmap)
        if el is not None and len(el) > 0:
            self.__dictionnaire["dec_fax"] = el[0].text

    def type_demande(self):
        return self.__type_demande

    def no_teleservice(self):
        return self.__no_teleservice

    def dictionnaire(self):
        return self.__dictionnaire

    def view_dictionnaire(self):
        for k in self.__dictionnaire.keys():
            print(k, ':', self.__dictionnaire[k])
