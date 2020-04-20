# Introduction

Afin de répondre à certaines demandes en interne j'avais développé ce plugin QGis pour traiter les XML des DT/DICT.

Le développement a été abandonnée durant plusieurs années, mais a repris grâce à l'intérêt porté par de nombreuses sollicitations et le travail fourni par la FDEA.

C'est à ce jour **la seule solution open source existante** sur le marché.

N'hésitez pas à nous contacter par [mail](mailto:infos@oslandia.com?subject=[DICT]%20Demande%20pour%20le%20plugin) si vous souhaitez faire évoluer ce plugin.

Vous trouverez plus d'informations sur notre [page dédiée](https://oslandia.com/en/offre-qgis/plugin-de-reponse-aux-dict).

# Utilisation

L'outil est composé de deux bouttons : un pour traiter un XML (à gauche) <img src="icon.png"  width="32" height="32"> et un pour configurer le plugin (à droite) <img src="config.png"  width="32" height="32">.

## Configuration
La configuration permet à l’utilisateur de ne pas avoir à répéter la saisie des informations et indiquer où et comment doivent sortir les PDF.

![configuration1](images/configuration.png)

![configuration2](images/configuration2.png)

## Traitement de la DT/DICT

Le XML reçu est à ouvrir via la boîte de dialogue suivante :

![chargement du xml](images/chargement_xml.png)

Le formulaire Cerfa 14435 est pré-rempli avec les informations du déclarant extraites après analyse du fichier XML et celles de l'exploitant saisies dans la boîte de diaalogue
de configuration. Le plugin vous permet alors de le compléter en l'ouvrant avec la visionneuse PDF définie par défaut dans le système d'exploitation.

Toute visionneuse supportant le format FDF (Acrobat Form Data Format) d'Adobe est utilisable:

![visionneuse, "Réponse à la DICT"](images/exemple.pdf)

**Le nom du PDF de réponse est constitué de la manière suivante:
<prefixe>-<type_demande>-<no_teleservice>-<suffixe>

Par exemple, avec la configuration ci-dessus, le PDF de réponse à la DT-DICT numéro 2020041064952S s'appellera :

récépissé_-DC-2020041064952S-2018.pdf

Une fois le formulaire rempli, il suffit de l'enregistrer. Suivant les capacités de votre visionneuse, vous pourrez également le signer (par exemple, si 
vous utilisez Acrobat Reader DC, avec l'outil de signature intégré matérialisé par une pointe de stylo plume).

![visionneuse, "Signature"](images/signature1.pdf)
  
Le plugin doit s'utiliser sur un projet ouvert comprenant vos réseaux et les composeurs d'impression qui seront utilisés pour la sortie des plans.
Après avoir rempli le formulaire, vous devez sélectionner le composeur pour l'impression PDF. Vous pouvez noter une emprise de chantier indiquant l'emprise de la demande.

![Sélection du composeur et emprise du chantier](images/selection_composeur.png)

Une fois le traitement effectué vous pouvez récupérer le formulaire pdf et les plans. Ils seront fusionnés si vous avez configuré cette option.

