# -*- coding: utf-8 -*-

'''
	Gaia Add-on
	Copyright (C) 2016 Gaia

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
'''

from resources.lib.extensions import database
from resources.lib.extensions import tools

class Searches(database.Database):

	Name = 'searches' # The name of the file. Update version number of the database structure changes.

	TypeMovies = 'movies'
	TypeShows = 'shows'
	TypeDocumentaries = 'documentaries'
	TypeShorts = 'shorts'
	TypePeople = 'people'

	def __init__(self):
		database.Database.__init__(self, self.Name)

	def _initialize(self):
		self._createAll('CREATE TABLE IF NOT EXISTS %s (terms TEXT, time INTEGER, kids INTEGER, UNIQUE(terms));', [self.TypeMovies, self.TypeShows, self.TypeDocumentaries, self.TypeShorts, self.TypePeople])

	def insert(self, searchType, searchTerms, searchKids = tools.Selection.TypeUndefined):
		searchTerms = searchTerms.strip()
		if searchTerms and len(searchTerms) > 0:
			existing = self._select('SELECT terms FROM %s WHERE terms = "%s";' % (searchType, searchTerms))
			if existing:
				self.update(searchType, searchTerms)
			else:
				self._insert('INSERT INTO %s (terms, time, kids) VALUES ("%s", %d, %d);' % (searchType, searchTerms, tools.Time.timestamp(), searchKids))

	def insertMovies(self, searchTerms, searchKids = tools.Selection.TypeUndefined):
		self.insert(self.TypeMovies, searchTerms, searchKids)

	def insertShows(self, searchTerms, searchKids = tools.Selection.TypeUndefined):
		self.insert(self.TypeShows, searchTerms, searchKids)

	def insertDocumentaries(self, searchTerms, searchKids = tools.Selection.TypeUndefined):
		self.insert(self.TypeDocumentaries, searchTerms, searchKids)

	def insertShorts(self, searchTerms, searchKids = tools.Selection.TypeUndefined):
		self.insert(self.TypeShorts, searchTerms, searchKids)

	def insertPeople(self, searchTerms, searchKids = tools.Selection.TypeUndefined):
		self.insert(self.TypePeople, searchTerms, searchKids)

	def update(self, searchType, searchTerms):
		searchTerms = searchTerms.strip()
		self._update('UPDATE %s SET time = %d WHERE terms = "%s";' % (searchType, tools.Time.timestamp(), searchTerms))

	def updateMovies(self, searchTerms):
		self.update(self.TypeMovies, searchTerms)

	def updateShows(self, searchTerms):
		self.update(self.TypeShows, searchTerms)

	def updateDocumentaries(self, searchTerms):
		self.update(self.TypeDocumentaries, searchTerms)

	def updateShorts(self, searchTerms):
		self.update(self.TypeShorts, searchTerms)

	def updatePeople(self, searchTerms):
		self.update(self.TypePeople, searchTerms)

	def retrieve(self, searchType, count = 30, kids = tools.Selection.TypeUndefined):
		if kids == tools.Selection.TypeUndefined: kids = ''
		else: kids = 'WHERE kids IS %d' % kids
		return self._select('SELECT terms, kids FROM %s %s ORDER BY time DESC LIMIT %d;' % (searchType, kids, count))

	def retrieveAll(self, count = 30, kids = tools.Selection.TypeUndefined):
		if kids == tools.Selection.TypeUndefined: kids = ''
		else: kids = 'WHERE kids IS %d' % kids
		return self._select('''
			SELECT type, terms, kids FROM
			(
				SELECT time, terms, kids, "%s" as type FROM %s
				UNION ALL
				SELECT time, terms, kids, "%s" as type FROM %s
				UNION ALL
				SELECT time, terms, kids, "%s" as type FROM %s
				UNION ALL
				SELECT time, terms, kids, "%s" as type FROM %s
				UNION ALL
				SELECT time, terms, kids, "%s" as type FROM %s
			)
			%s
			ORDER BY time DESC LIMIT %d;
		''' % (self.TypeMovies, self.TypeMovies, self.TypeShows, self.TypeShows, self.TypeDocumentaries, self.TypeDocumentaries, self.TypeShorts, self.TypeShorts, self.TypePeople, self.TypePeople, kids, count))

	def retrieveMovies(self, count = 30, kids = tools.Selection.TypeUndefined):
		if kids == tools.Selection.TypeUndefined: kids = ''
		else: kids = 'WHERE kids IS %d' % kids
		return self._select('''
			SELECT terms, kids, "%s" as type FROM %s
			%s
			ORDER BY time DESC LIMIT %d;
		''' % (self.TypeMovies, self.TypeMovies, kids, count))

	def retrieveShows(self, count = 30, kids = tools.Selection.TypeUndefined):
		if kids == tools.Selection.TypeUndefined: kids = ''
		else: kids = 'WHERE kids IS %d' % kids
		return self._select('''
			SELECT terms, kids, "%s" as type FROM %s
			%s
			ORDER BY time DESC LIMIT %d;
		''' % (self.TypeShows, self.TypeShows, kids, count))

	def retrieveDocumentaries(self, count = 30, kids = tools.Selection.TypeUndefined):
		if kids == tools.Selection.TypeUndefined: kids = ''
		else: kids = 'WHERE kids IS %d' % kids
		return self._select('''
			SELECT terms, kids, "%s" as type FROM %s
			%s
			ORDER BY time DESC LIMIT %d;
		''' % (self.TypeDocumentaries, self.TypeDocumentaries, kids, count))

	def retrieveShorts(self, count = 30, kids = tools.Selection.TypeUndefined):
		if kids == tools.Selection.TypeUndefined: kids = ''
		else: kids = 'WHERE kids IS %d' % kids
		return self._select('''
			SELECT terms, kids, "%s" as type FROM %s
			%s
			ORDER BY time DESC LIMIT %d;
		''' % (self.TypeShorts, self.TypeShorts, kids, count))

	def retrievePeople(self, count = 30, kids = tools.Selection.TypeUndefined):
		if kids == tools.Selection.TypeUndefined: kids = ''
		else: kids = 'WHERE kids IS %d' % kids
		return self._select('''
			SELECT terms, kids, "%s" as type FROM %s
			%s
			ORDER BY time DESC LIMIT %d;
		''' % (self.TypePeople, self.TypePeople, kids, count))
