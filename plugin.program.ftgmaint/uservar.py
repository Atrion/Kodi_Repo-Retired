import os, xbmc, xbmcaddon
import binascii
#########################################################
### User Edit Variables #################################
#########################################################
# Enable/Disable the text file caching with 'Yes' or 'No' and age being how often it rechecks in minutes
CACHETEXT      = 'Yes'
CACHEAGE       = 30

ADDON_ID       = xbmcaddon.Addon().getAddonInfo('id')
ADDONTITLE     = '[COLOR yellow]-[COLOR blue][B]FTG Maintenance[/B][COLOR yellow]-[/COLOR]'
BUILDERNAME    = 'FTG'
ADVANCEDFILE   = 'http://'
EXCLUDES       = [ADDON_ID, 'repository.firetvguru', 'My_Builds', 'backupdir']
UPDATECHECK    = 0
PATH           = xbmcaddon.Addon().getAddonInfo('path')
ART            = os.path.join(PATH, 'resources', 'art')

#########################################################
### THEMING MENU ITEMS ##################################
#########################################################
# If you want to use locally stored icons the place them in the Resources/Art/
# folder of the wizard then use os.path.join(ART, 'imagename.png')
# do not place quotes around os.path.join
# Example:  ICONMAINT     = os.path.join(ART, 'mainticon.png')
#           ICONSETTINGS  = 'http://aftermathwizard.net/repo/wizard/settings.png'
# Leave as http:// for default icon
ICONBUILDS     = 'http://i.imgur.com/E7oBc7x.png'
ICONMAINT      = 'http://i.imgur.com/E7oBc7x.png'
ICONAPK        = 'http://i.imgur.com/E7oBc7x.png'
ICONADDONS     = 'http://i.imgur.com/E7oBc7x.png'
ICONYOUTUBE    = 'http://i.imgur.com/E7oBc7x.png'
ICONSAVE       = 'http://i.imgur.com/E7oBc7x.png'
ICONTRAKT      = 'http://i.imgur.com/E7oBc7x.png'
ICONREAL       = 'http://i.imgur.com/E7oBc7x.png'
ICONLOGIN      = 'http://i.imgur.com/E7oBc7x.png'
ICONCONTACT    = 'http://i.imgur.com/E7oBc7x.png'
ICONSETTINGS   = 'http://i.imgur.com/E7oBc7x.png'
# Hide the ====== seperators 'Yes' or 'No'
HIDESPACERS    = 'No'
# Character used in seperator
SPACER         = '~'

# You can edit these however you want, just make sure that you have a %s in each of the
# THEME's so it grabs the text from the menu item
COLOR1         = 'blue'
COLOR2         = 'yellow'
COLOR3         = 'red'
COLOR4         = 'snow'
COLOR5         = 'lime'
# Primary menu items   / %s is the menu item and is required
THEME1         = '[COLOR '+COLOR1+']%s[/COLOR]'
# Build Names          / %s is the menu item and is required
THEME2         = '[COLOR '+COLOR1+']%s[/COLOR]'
# Alternate items      / %s is the menu item and is required
THEME3         = '[COLOR '+COLOR2+']%s[/COLOR]'
# Current Build Header / %s is the menu item and is required
THEME4         = '[COLOR '+COLOR2+']Current Build:[/COLOR] [COLOR '+COLOR2+']%s[/COLOR]'
# Current Theme Header / %s is the menu item and is required
THEME5         = '[COLOR '+COLOR2+']Current Theme:[/COLOR] [COLOR '+COLOR2+']%s[/COLOR]'
THEME6         = '[COLOR '+COLOR3+'][B]%s[/B][/COLOR]'

# Message for Contact Page
# Enable 'Contact' menu item 'Yes' hide or 'No' dont hide
HIDECONTACT    = 'No'
#########################################################

#########################################################
### AUTO UPDATE #########################################
########## FOR THOSE WITH NO REPO #######################
# Enable Auto Update 'Yes' or 'No'
AUTOUPDATE     = 'No'
# Url to wizard version
WIZARDFILE     = 'http://'
#########################################################

#########################################################
### AUTO INSTALL ########################################
########## REPO IF NOT INSTALLED ########################
# Enable Auto Install 'Yes' or 'No'
AUTOINSTALL    = 'Yes'
# Addon ID for the repository
REPOID         = 'repository.firetvguru'
# Url to Addons.xml file in your repo folder(this is so we can get the latest version)
REPOADDONXML   = binascii.unhexlify('68747470733a2f2f7261772e67697468756275736572636f6e74656e742e636f6d2f466972657476677572752f666972652d74762f6d61737465722f7265706f7369746f72792e666972657476677572752f6164646f6e2e786d6c')
# Url to folder zip is located in
REPOZIPURL     = binascii.unhexlify('68747470733a2f2f6769746875622e636f6d2f466972657476677572752f666972652d74762f7261772f6d61737465722f7265706f7369746f72792e666972657476677572752f')
#########################################################
############################    #############################