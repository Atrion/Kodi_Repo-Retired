# -*- coding: utf-8 -*-

"""
	Orion
	 https://orionoid.com

	This program is free software: you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation, either version 3 of the License, or
	(at your option) any later version.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

"""

########################################################################################################################################
# FOR DEVELOPERS
########################################################################################################################################

To use the Orion Kodi addon, do the following:
	1. Add Orion as a dependency to your addon.xml:
			<import addon="script.module.orion" version="1.0.0" />
	2. Import the Orion module in your Python script:
			from orion import *
	3. Create a new Orion object with your app API key:
			orion = Orion('my_app_key')
	4. Search for the streams using the instance from the previous step:
			results = orion.streams(type = Orion.TypeMovie, idXYZ = 'Orion, IMDb, TMDb, or TVDb ID')

A few things to note:
	1. Do not name your file "orion.py" or your class "Orion", because this will clash with Orion's import.
	2. A query requires a "type" and either and ID (idOrion, idImdb, idTmdb, idTvdb) or the "query" parameter.
		In addition, if you search for a show, you have to provide the "numberSeason" and "numberEpisode" together with the ID.

########################################################################################################################################

STREAM EXAMPLE 1 - Retrieve a movie using an IMDb ID.

	from orion import *
	result = Orion('my_app_key').streams(type = Orion.TypeMovie, idImdb = '0063350')

########################################################################################################################################

STREAM EXAMPLE 2 - Retrieve an episode using a TVDb ID.

	from orion import *
	result = Orion('my_app_key').streams(type = Orion.TypeShow, idTvdb = '73739', numberSeason = 3, numberEpisode = 5)

########################################################################################################################################

STREAM EXAMPLE 3 - Retrieve a movie using a query string. Using a query is not advised, since the wrong results might be returned.

	from orion import *
	result = Orion('my_app_key').streams(type = Orion.TypeMovie, query = 'Night of the Living Dead 1968')

########################################################################################################################################

STREAM EXAMPLE 4 - Retrieve a movie no larger than 2GB and being either a direct hoster link or cached on Premiumize.

	from orion import *
	result = Orion('my_app_key').streams(type = Orion.TypeMovie, idImdb = '0063350', fileSize = [None, 2147483648], access = [Orion.AccessDirect, Orion.AccessPremiumize])

########################################################################################################################################

STREAM EXAMPLE 5 - Retrieve a movie that has a video quality between SD and HD1080, and a DD or DTS audio codec.

	from orion import *
	result = Orion('my_app_key').streams(type = Orion.TypeMovie, idImdb = '0063350', videoQuality = [Orion.QualitySd, Orion.QualityHd1080], audioCodec = [Orion.CodecDd, Orion.CodecDts])

########################################################################################################################################

STREAM EXAMPLE 6 - Retrieve a movie that has a popularity of at least 50% and sorted by file size in descending order.

	from orion import *
	result = Orion('my_app_key').streams(type = Orion.TypeMovie, idImdb = '0063350', popularityPercent = 0.5, sortValue = Orion.SortFileSize, sortOrder = Orion.OrderDescending)

########################################################################################################################################

STREAM EXAMPLE 7 - Retrieve a movie with a maximum of 100 links and a page offset of 2 (that is link number 101 - 200).

	from orion import *
	result = Orion('my_app_key').streams(type = Orion.TypeMovie, idImdb = '0063350', limitCount = 100, limitPage = 2)

########################################################################################################################################

LINK - Retrieve Orion's website URL.

	from orion import *
	result = Orion('my_app_key').link()

########################################################################################################################################

APP DETAILS - Retrieve your app details and status.

	from orion import *
	result = Orion('my_app_key').app()

########################################################################################################################################

APP VALID - Check if your app key and status is valid.

	from orion import *
	result = Orion('my_app_key').appValid()

########################################################################################################################################

APP DIALOG - Show a Kodi dialog with your app details.

	from orion import *
	result = Orion('my_app_key').appDialog()

########################################################################################################################################

USER DETAILS - Retrieve your user details and status.

	from orion import *
	result = Orion('my_app_key').user()

########################################################################################################################################

USER VALID - Check if the user key and status is valid.

	from orion import *
	result = Orion('my_app_key').userValid()

########################################################################################################################################

USER FREE - Check if the user has a free account.

	from orion import *
	result = Orion('my_app_key').userFree()

########################################################################################################################################

USER PREMIUM - Check if the user has a premium account.

	from orion import *
	result = Orion('my_app_key').userPremium()

########################################################################################################################################

USER DIALOG - Show a Kodi dialog with the user details.

	from orion import *
	result = Orion('my_app_key').userDialog()

########################################################################################################################################

SERVER STATS - Retrieve the Orion server stats.

	from orion import *
	result = Orion('my_app_key').serverStats()

########################################################################################################################################

SERVER DIALOG - Show a Kodi dialog with the Orion server stats.

	from orion import *
	result = Orion('my_app_key').serverDialog()

########################################################################################################################################

SERVER TEST - Test if the Orion server is up and running.

	from orion import *
	result = Orion('my_app_key').serverTest()

########################################################################################################################################

"""

from orion.modules.orionapi import *
from orion.modules.orionapp import *
from orion.modules.orionuser import *
from orion.modules.orionstats import *
from orion.modules.oriontools import *
from orion.modules.orionitem import *
from orion.modules.orionsettings import *
from orion.modules.orionnavigator import *

class Orion:

	##############################################################################
	# CONSTANTS
	##############################################################################

	Id = 'script.module.orion'
	Name = 'Orion'

	# Encoding
	EncodingJson = 'json'									# JSON String (encoded JSON)
	EncodingStruct = 'struct'								# Python dictionary/map (decoded JSON)
	EncodingObject = 'object'								# Orion classes (object oriented)
	EncodingDefault = EncodingStruct

	# Filter Type
	FilterNone = OrionItem.FilterNone 						# Do not use any filter at all
	FilterSettings = OrionItem.FilterSettings				# Use the filters set by the user in the Orion addon settings

	# Item Type
	TypeMovie = OrionItem.TypeMovie							# 'movie'			(Movie streams)
	TypeShow = OrionItem.TypeShow							# 'show'			(Epsiode streams)

	# Stream Access
	AccessDirect = OrionItem.AccessDirect					# 'direct'			(Direct hoster link)
	AccessIndirect = OrionItem.AccessIndirect				# 'indirect'		(Indirect hoster link)
	AccessPremiumize = OrionItem.AccessPremiumize			# 'premiumize'		(Cached on Premiumize)
	AccessOffcloud = OrionItem.AccessOffcloud				# 'offcloud'		(Cached on OffCloud)
	AccessRealdebrid = OrionItem.AccessRealdebrid			# 'realdebrid'		(Cached on RealDebrid)

	# Stream Type
	StreamTorrent = OrionStream.TypeTorrent					# 'torrent'			(Torrent magnet or link)
	StreamUsenet = OrionStream.TypeUsenet					# 'usenet'			(Usenet NZB link)
	StreamHoster = OrionStream.TypeHoster					# 'hoster'			(File hoster link)

	# Video Quality
	QualityHd8k = OrionStream.QualityHd8k					# 'hd8k'			(High Definition 8k)
	QualityHd6k = OrionStream.QualityHd6k					# 'hd6k'			(High Definition 6k)
	QualityHd4k = OrionStream.QualityHd4k					# 'hd4k'			(High Definition 4k)
	QualityHd2k = OrionStream.QualityHd2k					# 'hd2k'			(High Definition 2k)
	QualityHd1080 = OrionStream.QualityHd1080				# 'hd1080'			(High Definition 1080p)
	QualityHd720 = OrionStream.QualityHd720					# 'hd720'			(High Definition 720p)
	QualitySd = OrionStream.QualitySd						# 'sd'				(Standard Definition 240p, 360, 480p)
	QualityScr1080 = OrionStream.QualityScr1080				# 'scr1080'			(Screener 1080p)
	QualityScr720 = OrionStream.QualityScr720				# 'scr720'			(Screener 720p)
	QualityScr = OrionStream.QualityScr						# 'scr'				(Screener)
	QualityCam1080 = OrionStream.QualityCam1080				# 'cam1080'			(Camera Recording 1080p)
	QualityCam720 = OrionStream.QualityCam720				# 'cam720'			(Camera Recording 720p)
	QualityCam = OrionStream.QualityCam						# 'cam'				(Camera Recording)

	# Video Codec
	CodecH266 = OrionStream.CodecH266						# 'h266'			(Moving Picture Experts Group Future Video Codec)
	CodecH265 = OrionStream.CodecH265						# 'h265'			(Moving Picture Experts Group High Efficiency Video Coding)
	CodecH264 = OrionStream.CodecH264						# 'h264'			(Moving Picture Experts Group Advanced Video Coding)
	CodecH262 = OrionStream.CodecH262						# 'h262'			(Moving Picture Experts Group Part 2)
	CodecH222 = OrionStream.CodecH222						# 'h222'			(Moving Picture Experts Group Part 1)
	Codec3gp = OrionStream.Codec3gp							# '3gp'				(Third Generation Partnership Project)
	CodecAvi = OrionStream.CodecAvi							# 'avi'				(Audio Video Interleave)
	CodecDivx = OrionStream.CodecDivx						# 'divx'			(DivX Video)
	CodecFlv = OrionStream.CodecFlv							# 'flv'				(Flash Video)
	CodecMkv = OrionStream.CodecMkv							# 'mkv'				(Matroska Multimedia Container)
	CodecMov = OrionStream.CodecMov							# 'mov'				(QuickTime File Format)
	CodecMpeg = OrionStream.CodecMpeg						# 'mpeg'			(Moving Picture Experts Group)
	CodecWmv = OrionStream.CodecWmv							# 'wmv'				(Windows Media Video)
	CodecXvid = OrionStream.CodecXvid						# 'xvid'			(XviD)

	# Release Type
	ReleaseBdrip = OrionStream.ReleaseBdrip					# 'bdrip'			(BluRay Rip)
	ReleaseBdscr = OrionStream.ReleaseBdscr					# 'bdscr'			(BluRay Screener)
	ReleaseBluray = OrionStream.ReleaseBluray				# 'bluray'			(BluRay)
	ReleaseCam = OrionStream.ReleaseCam						# 'cam'				(Camera)
	ReleaseDdc = OrionStream.ReleaseDdc						# 'ddc'				(Direct Digital Content)
	ReleaseDvd = OrionStream.ReleaseDvd						# 'dvd'				(DVD)
	ReleaseDvdrip = OrionStream.ReleaseDvdrip				# 'dvdrip'			(DVD Rip)
	ReleaseDvdscr = OrionStream.ReleaseDvdscr				# 'dvdscr'			(DVD Screener)
	ReleaseHdrip = OrionStream.ReleaseHdrip					# 'hdrip'			(HD Rip)
	ReleaseHdts = OrionStream.ReleaseHdts					# 'hdts'			(HD Telesync)
	ReleaseHdtv = OrionStream.ReleaseHdtv					# 'hdtv'			(HD Television)
	ReleasePdvd = OrionStream.ReleasePdvd					# 'pdvd'			(PDVD)
	ReleasePpv = OrionStream.ReleasePpv						# 'ppv'				(Pay Per View)
	ReleaseR5 = OrionStream.ReleaseR5						# 'r5'				(Region 5)
	ReleaseScr = OrionStream.ReleaseScr						# 'scr'				(Screener)
	ReleaseTk = OrionStream.ReleaseTk						# 'tk'				(Telecine)
	ReleaseTs = OrionStream.ReleaseTs						# 'ts'				(Telesync)
	ReleaseTvrip = OrionStream.ReleaseTvrip					# 'tvrip'			(Television Rip)
	ReleaseVcd = OrionStream.ReleaseVcd						# 'vcd'				(Virtual CD)
	ReleaseVhs = OrionStream.ReleaseVhs						# 'vhs'				(VHS)
	ReleaseVhsrip = OrionStream.ReleaseVhsrip				# 'vhsrip'			(VHS Rip)
	ReleaseWebcap = OrionStream.ReleaseWebcap				# 'webcap'			(Web Capture)
	ReleaseWebdl = OrionStream.ReleaseWebdl					# 'webdl'			(Web Download)
	ReleaseWebrip = OrionStream.ReleaseWebrip				# 'webrip'			(Web Rip)
	ReleaseWp = OrionStream.ReleaseWp						# 'wp'				(Workprint)

	# Uploader Name
	Uploader8bit = OrionStream.Uploader8bit					# '8bit'			(8bit)
	Uploader10bit = OrionStream.Uploader10bit				# '10bit'			(10bit)
	UploaderAaf = OrionStream.UploaderAaf					# 'aaf'				(aAF)
	UploaderAdrenaline = OrionStream.UploaderAdrenaline		# 'adrenaline'		(ADRENALiNE)
	UploaderAfg = OrionStream.UploaderAfg					# 'afg'				(AFG)
	UploaderAvs = OrionStream.UploaderAvs					# 'avs'				(AVS)
	UploaderBatv = OrionStream.UploaderBatv					# 'batv'			(BATV)
	UploaderBrisk = OrionStream.UploaderBrisk				# 'brisk'			(BRISK)
	UploaderC4tv = OrionStream.UploaderC4tv					# 'c4tv'			(C4TV)
	UploaderCmrg = OrionStream.UploaderCmrg					# 'cmrg'			(CMRG)
	UploaderCpg = OrionStream.UploaderCpg					# 'cpg'				(CPG)
	UploaderCravers = OrionStream.UploaderCravers			# 'cravers'			(CRAVERS)
	UploaderCrimson = OrionStream.UploaderCrimson			# 'crimson'			(CRiMSON)
	UploaderCrooks = OrionStream.UploaderCrooks				# 'crooks'			(CROOKS)
	UploaderCtrlhd = OrionStream.UploaderCtrlhd				# 'ctrlhd'			(CtrlHD)
	UploaderD3g = OrionStream.UploaderD3g					# 'd3g'				(d3g)
	UploaderDeadpool = OrionStream.UploaderDeadpool			# 'deadpool'		(DEADPOOL)
	UploaderDeejayahmed = OrionStream.UploaderDeejayahmed	# 'deejayahmed'		(DeeJayAhmed)
	UploaderDeflate = OrionStream.UploaderDeflate			# 'deflate'			(DEFLATE)
	UploaderDemand = OrionStream.UploaderDemand				# 'demand'			(DEMAND)
	UploaderDhd = OrionStream.UploaderDhd					# 'dhd'				(DHD)
	UploaderDiamond = OrionStream.UploaderDiamond			# 'diamond'			(DIAMOND)
	UploaderDublado = OrionStream.UploaderDublado			# 'dublado'			(Dublado)
	UploaderEbi = OrionStream.UploaderEbi					# 'ebi'				(Ebi)
	UploaderEpub = OrionStream.UploaderEpub					# 'epub'			(EPUB)
	UploaderEsc = OrionStream.UploaderEsc					# 'esc'				(eSc)
	UploaderEthd = OrionStream.UploaderEthd					# 'ethd'			(EtHD)
	UploaderEtrg = OrionStream.UploaderEtrg					# 'etrg'			(ETRG)
	UploaderEttv = OrionStream.UploaderEttv					# 'ettv'			(ETTV)
	UploaderEvo = OrionStream.UploaderEvo					# 'evo'				(EVO)
	UploaderExclusive = OrionStream.UploaderExclusive		# 'exclusive'		(Exclusive)
	UploaderExyu = OrionStream.UploaderExyu					# 'exyu'			(ExYu)
	UploaderEztv = OrionStream.UploaderEztv					# 'eztv'			(EZTV)
	UploaderFgt = OrionStream.UploaderFgt					# 'fgt'				(FGT)
	UploaderFightbb = OrionStream.UploaderFightbb			# 'fightbb'			(FightBB)
	UploaderFleet = OrionStream.UploaderFleet				# 'fleet'			(FLEET)
	UploaderFlt = OrionStream.UploaderFlt					# 'flt'				(FLT)
	UploaderFqm = OrionStream.UploaderFqm					# 'fqm'				(FQM)
	UploaderFreebee = OrionStream.UploaderFreebee			# 'freebee'			(Freebee)
	UploaderFs = OrionStream.UploaderFs						# 'fs'				(FS)
	UploaderFum = OrionStream.UploaderFum					# 'fum'				(FUM)
	UploaderGeckos = OrionStream.UploaderGeckos				# 'geckos'			(GECKOS)
	UploaderGirays = OrionStream.UploaderGirays				# 'girays'			(GIRAYS)
	UploaderGooner = OrionStream.UploaderGooner				# 'gooner'			(Gooner)
	UploaderGush = OrionStream.UploaderGush					# 'gush'			(GUSH)
	UploaderGwc = OrionStream.UploaderGwc					# 'gwc'				(GWC)
	UploaderHdsector = OrionStream.UploaderHdsector			# 'hdsector'		(HDSector)
	UploaderHeel = OrionStream.UploaderHeel					# 'heel'			(HEEL)
	UploaderHivecm8 = OrionStream.UploaderHivecm8			# 'hivecm8'			(HiveCM8)
	UploaderHon3y = OrionStream.UploaderHon3y				# 'hon3y'			(Hon3y)
	UploaderHqmic = OrionStream.UploaderHqmic				# 'hqmic'			(HQMic)
	UploaderIextv = OrionStream.UploaderIextv				# 'iextv'			(iExTV)
	UploaderIft = OrionStream.UploaderIft					# 'ift'				(iFT)
	UploaderIon10 = OrionStream.UploaderIon10				# 'ion10'			(ION10)
	UploaderIsm = OrionStream.UploaderIsm					# 'ism'				(iSm)
	UploaderJive = OrionStream.UploaderJive					# 'jive'			(JIVE)
	UploaderJoy = OrionStream.UploaderJoy					# 'joy'				(Joy)
	UploaderJyk = OrionStream.UploaderJyk					# 'jyk'				(JYK)
	UploaderKillers = OrionStream.UploaderKillers			# 'killers'			(KILLERS)
	UploaderLegi0n = OrionStream.UploaderLegi0n				# 'legi0n'			(LEGi0N)
	UploaderLol = OrionStream.UploaderLol					# 'lol'				(LOL)
	UploaderM3d = OrionStream.UploaderM3d					# 'm3d'				(M3D)
	UploaderManning = OrionStream.UploaderManning			# 'manning'			(Manning)
	UploaderMegusta = OrionStream.UploaderMegusta			# 'megusta'			(MeGusta)
	UploaderMkvcage = OrionStream.UploaderMkvcage			# 'mkvcage'			(MkvCage)
	UploaderMonrose = OrionStream.UploaderMonrose			# 'monrose'			(MONROSE)
	UploaderMoritz = OrionStream.UploaderMoritz				# 'moritz'			(MORiTZ)
	UploaderMrn = OrionStream.UploaderMrn					# 'mrn'				(MRN)
	UploaderMtb = OrionStream.UploaderMtb					# 'mtb'				(MTB)
	UploaderMulvacoded = OrionStream.UploaderMulvacoded		# 'mulvacoded'		(MULVAcoded)
	UploaderN1c = OrionStream.UploaderN1c					# 'n1c'				(N1C)
	UploaderNezu = OrionStream.UploaderNezu					# 'nezu'			(NeZu)
	UploaderNtb = OrionStream.UploaderNtb					# 'ntb'				(NTb)
	UploaderNtg = OrionStream.UploaderNtg					# 'ntg'				(NTG)
	UploaderNvee = OrionStream.UploaderNvee					# 'nvee'			(NVEE)
	UploaderOrganic = OrionStream.UploaderOrganic			# 'organic'			(ORGANiC)
	UploaderPimprg = OrionStream.UploaderPimprg				# 'pimprg'			(pimprg)
	UploaderPlutonium = OrionStream.UploaderPlutonium		# 'plutonium'		(PLUTONiUM)
	UploaderPsa = OrionStream.UploaderPsa					# 'psa'				(PSA)
	UploaderPublichd = OrionStream.UploaderPublichd			# 'publichd'		(PublicHD)
	UploaderQpel = OrionStream.UploaderQpel					# 'qpel'			(QPEL)
	UploaderRarbg = OrionStream.UploaderRarbg				# 'rarbg'			(RARBG)
	UploaderRartv = OrionStream.UploaderRartv				# 'rartv'			(RARTV)
	UploaderReenc = OrionStream.UploaderReenc				# 'reenc'			(ReEnc)
	UploaderReward = OrionStream.UploaderReward				# 'reward'			(REWARD)
	UploaderRick = OrionStream.UploaderRick					# 'rick'			(RiCK)
	UploaderRmteam = OrionStream.UploaderRmteam				# 'rmteam'			(RMTeam)
	UploaderSdi = OrionStream.UploaderSdi					# 'sdi'				(SDI)
	UploaderSecretos = OrionStream.UploaderSecretos			# 'secretos'		(SECRETOS)
	UploaderShaanig = OrionStream.UploaderShaanig			# 'shaanig'			(ShAaNiG)
	UploaderSkgtv = OrionStream.UploaderSkgtv				# 'skgtv'			(SKGTV)
	UploaderSparks = OrionStream.UploaderSparks				# 'sparks'			(SPARKS)
	UploaderSpc = OrionStream.UploaderSpc					# 'spc'				(SPC)
	UploaderStrife = OrionStream.UploaderStrife				# 'strife'			(STRiFE)
	UploaderStuttershit = OrionStream.UploaderStuttershit	# 'stuttershit'		(STUTTERSHIT)
	UploaderSujaidr = OrionStream.UploaderSujaidr			# 'sujaidr'			(Sujaidr)
	UploaderSva = OrionStream.UploaderSva					# 'sva'				(SVA)
	UploaderTbs = OrionStream.UploaderTbs					# 'tbs'				(TBS)
	UploaderTitan = OrionStream.UploaderTitan				# 'titan'			(TiTAN)
	UploaderTjet = OrionStream.UploaderTjet					# 'tjet'			(TJET)
	UploaderTomcat12 = OrionStream.UploaderTomcat12			# 'tomcat12'		(tomcat12)
	UploaderTopkek = OrionStream.UploaderTopkek				# 'topkek'			(TOPKEK)
	UploaderTvc = OrionStream.UploaderTvc					# 'tvc'				(TVC)
	UploaderUav = OrionStream.UploaderUav					# 'uav'				(UAV)
	UploaderUnveil = OrionStream.UploaderUnveil				# 'unveil'			(UNVEiL)
	UploaderUtr = OrionStream.UploaderUtr					# 'utr'				(UTR)
	UploaderVain = OrionStream.UploaderVain					# 'vain'			(VAiN)
	UploaderViethd = OrionStream.UploaderViethd				# 'viethd'			(VietHD)
	UploaderVppv = OrionStream.UploaderVppv					# 'vppv'			(VPPV)
	UploaderW4f = OrionStream.UploaderW4f					# 'w4f'				(W4F)
	UploaderWwrg = OrionStream.UploaderWwrg					# 'wwrg'			(WWRG)
	UploaderX0r = OrionStream.UploaderX0r					# 'x0r'				(x0r)
	UploaderXrg = OrionStream.UploaderXrg					# 'xrg'				(xRG)
	UploaderYifi = OrionStream.UploaderYifi					# 'yifi'			(YIFI)
	UploaderYts = OrionStream.UploaderYts					# 'yts'				(YTS)

	# Edition Type
	EditionNone = OrionStream.EditionNone					# None				(Normal cinema version)
	EditionExtended = OrionStream.EditionExtended			# 'extended'		(Extended editions and director cuts)

	# Audio Type
	AudioStandard = OrionStream.AudioStandard				# 'standard'		(Standard non-dubbed audio)
	AudioDubbed = OrionStream.AudioDubbed					# 'dubbed'			(Dubbed or voiced-over audio)

	# Audio Codec
	CodecDd = OrionStream.CodecDd							# 'dd'				(Dolby Digital)
	CodecDts = OrionStream.CodecDts							# 'dts'				(Dedicated To Sound)
	CodecDra = OrionStream.CodecDra							# 'dra'				(Dynamic Resolution Adaptation)
	CodecAac = OrionStream.CodecAac							# 'aac'				(Advanced Audio Coding)
	CodecFlac = OrionStream.CodecFlac						# 'flac'			(Free Lossless Audio Codec)
	CodecMp3 = OrionStream.CodecMp3							# 'mp3'				(Moving Picture Experts Group Audio Layer III)
	CodecPcm = OrionStream.CodecPcm							# 'pcm'				(Pulse-Code Modulation)

	# Audio Channels
	Channels1 = OrionStream.Channels1						# 1					(Mono)
	Channels2 = OrionStream.Channels2						# 2					(Stereo)
	Channels6 = OrionStream.Channels6						# 6					(5.1 Surround Sound)
	Channels8 = OrionStream.Channels8						# 8					(7.1 Surround Sound)

	# Subtitle Type
	SubtitleNone = OrionStream.SubtitleNone					# None				(No subtitles)
	SubtitleSoft = OrionStream.SubtitleSoft					# 'soft'			(Soft-coded subtitles that can be disabled)
	SubtitleHard = OrionStream.SubtitleHard					# 'hard'			(Soft-coded subtitles that cannot be disabled)

	# Sorting Value
	SortShuffle = OrionItem.SortShuffle						# 'shuffle'			(Randomly shuffle results)
	SortPopularity = OrionItem.SortPopularity				# 'popularity'		(Sort by popularity)
	SortTimeAdded = OrionItem.SortTimeAdded					# 'timeadded'		(Sort by time first added)
	SortTimeUpdated = OrionItem.SortTimeUpdated				# 'timeupdated'		(Sort by time last updated)
	SortVideoQuality = OrionItem.SortVideoQuality			# 'videoquality'	(Sort by video quality)
	SortAudioChannels = OrionItem.SortAudioChannels			# 'audiochannels'	(Sort by audio channel count)
	SortFileSize = OrionItem.SortFileSize					# 'filesize'		(Sort by file size)
	SortStreamSeeds = OrionItem.SortStreamSeeds				# 'streamseeds'		(Sort by torrent seed count)
	SortStreamAge = OrionItem.SortStreamAge					# 'streamage'		(Sort by usenet age)

	# Sorting Order
	OrderAscending = OrionItem.OrderAscending				# 'ascending'		(Order by low to high)
	OrderDescending = OrionItem.OrderDescending				# 'descending'		(Order from high to low)

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self, key, encoding = EncodingDefault, silent = False):
		self.mApp = OrionApp.instance(key)
		OrionSettings.silentSet(silent)
		self.mApp.refresh() # Must be done here instead of the instance function, otherwise the is recursion with the API.
		self.mEncoding = encoding

	##############################################################################
	# ENCODING
	##############################################################################

	def _encode(self, object, encoding = None):
		if encoding == None: encoding = self.mEncoding
		if object == None: return '' if encoding == self.EncodingJson else None
		elif encoding == self.EncodingJson:
			if OrionTools.isArray(object): return [OrionTools.jsonTo(i.data()) for i in object]
			else: return OrionTools.jsonTo(object.data())
		elif encoding == self.EncodingStruct:
			if OrionTools.isArray(object): return [i.data() for i in object]
			else: return object.data()
		else: return object

	##############################################################################
	# LINK
	##############################################################################

	def link(self):
		return OrionTools.link()

	##############################################################################
	# SETTINGS
	##############################################################################

	def settingsScrapingTimeout(self):
		return OrionSettings.getGeneralScrapingTimeout()

	def settingsScrapingMode(self):
		return OrionSettings.getGeneralScrapingMode()

	def settingsScrapingCount(self):
		return OrionSettings.getGeneralScrapingCount()

	def settingsScrapingQuality(self):
		return OrionSettings.getGeneralScrapingQuality()

	##############################################################################
	# APP
	##############################################################################

	def app(self, encoding = None):
		return self._encode(self.mApp, encoding = encoding)

	def appValid(self):
		return self.mApp.valid()

	def appDialog(self):
		return OrionNavigator.dialogApp()

	##############################################################################
	# USER
	##############################################################################

	def user(self, encoding = None):
		return self._encode(OrionUser.instance(), encoding = encoding)

	def userEnabled(self):
		return OrionUser.instance().enabled()

	def userValid(self):
		return OrionUser.instance().valid()

	def userFree(self):
		return OrionUser.instance().subscriptionPackageFree()

	def userPremium(self):
		return OrionUser.instance().subscriptionPackagePremium()

	def userDialog(self):
		return OrionNavigator.dialogUser()

	def userUpdate(self, key = None, input = False, loader = False):
		if input:
			key = OrionNavigator.settingsAccountKey()
		if key:
			user = OrionUser.instance()
			if not key == None: user.settingsKeySet(key)
			return OrionNavigator.settingsAccountRefresh(launch = False, loader = True, notification = True)
		else:
			return False

	##############################################################################
	# SERVER
	##############################################################################

	def serverStats(self, encoding = None):
		stats = OrionStats.instance()
		stats.update()
		return self._encode(stats, encoding = encoding)

	def serverDialog(self):
		return OrionNavigator.dialogServer()

	def serverTest(self):
		return OrionApi().serverTest()

	##############################################################################
	# STREAMS
	##############################################################################

	def streams(self,

				type,

				query = None,

				idOrion = None,
				idImdb = None,
				idTmdb = None,
				idTvdb = None,

				numberSeason = None,
				numberEpisode = None,

				limitCount = FilterSettings,
				limitRetry = FilterSettings,
				limitOffset = FilterSettings,
				limitPage = FilterSettings,

				timeAdded = FilterSettings,
				timeAddedAge = FilterSettings,
				timeUpdated = FilterSettings,
				timeUpdatedAge = FilterSettings,

				sortValue = FilterSettings,
				sortOrder = FilterSettings,

				popularityPercent = FilterSettings,
				popularityCount = FilterSettings,

				streamType = FilterSettings,
				streamSource = FilterSettings,
				streamHoster = FilterSettings,
				streamSeeds = FilterSettings,
				streamAge = FilterSettings,

				access = FilterSettings,

				fileSize = FilterSettings, # Can be a single value holding the maximum size (eg: 1073741824), or a tuple/list with the minimum and maximum sizes (eg: [536870912,1073741824]). If either value is None, there is no upper/lower bound (eg: [536870912,None])
				fileUnknown = FilterSettings,
				filePack = FilterSettings,

				metaRelease = FilterSettings,
				metaUploader = FilterSettings,
				metaEdition = FilterSettings,

				videoQuality = FilterSettings,
				videoCodec = FilterSettings,
				video3D = FilterSettings,

				audioType = FilterSettings,
				audioChannels = FilterSettings,
				audioCodec = FilterSettings,
				audioLanguages = FilterSettings,

				subtitleType = FilterSettings,
				subtitleLanguages = FilterSettings,

				item = None,

				details = False,
				encoding = None
		):
		result = OrionItem.retrieve(
			type = type,

			query = query,

			idOrion = idOrion,
			idImdb = idImdb,
			idTmdb = idTmdb,
			idTvdb = idTvdb,

			numberSeason = numberSeason,
			numberEpisode = numberEpisode,

			limitCount = limitCount,
			limitRetry = limitRetry,
			limitOffset = limitOffset,
			limitPage = limitPage,

			timeAdded = timeAdded,
			timeAddedAge = timeAddedAge,
			timeUpdated = timeUpdated,
			timeUpdatedAge = timeUpdatedAge,

			sortValue = sortValue,
			sortOrder = sortOrder,

			popularityPercent = popularityPercent,
			popularityCount = popularityCount,

			streamType = streamType,
			streamSource = streamSource,
			streamHoster = streamHoster,
			streamSeeds = streamSeeds,
			streamAge = streamAge,

			access = access,

			fileSize = fileSize,
			fileUnknown = fileUnknown,
			filePack = filePack,

			metaRelease = metaRelease,
			metaUploader = metaUploader,
			metaEdition = metaEdition,

			videoQuality = videoQuality,
			videoCodec = videoCodec,
			video3D = video3D,

			audioType = audioType,
			audioChannels = audioChannels,
			audioCodec = audioCodec,
			audioLanguages = audioLanguages,

			subtitleType = subtitleType,
			subtitleLanguages = subtitleLanguages,

			item = item
		)
		if not details: result = result.streams()
		return self._encode(result, encoding = encoding)

	def streamsCount(self, streams, quality = FilterNone):
		if quality == self.FilterSettings: quality = self.settingsScrapingQuality()
		return OrionStream.count(streams = streams, quality = quality)
