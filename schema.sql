drop table if exists words;
create table words (
  id integer primary key autoincrement,
  word string not null
);


drop table if exists urls;
create table urls (
  id integer primary key autoincrement,
  url string not null
);


drop table if exists word_index;
create table word_index (
  id integer primary key autoincrement,
  word_id integer,
  url_id integer
);