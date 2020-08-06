const SQL = require('sql-template-strings');
const sqlite = require('sqlite');
const path = require('path');
const category = require('./category');

const databasePath = path.resolve(__dirname, '../database/garbage.sqlite');

async function getDb() {
  const db = await sqlite.open(databasePath, {
    cached: true,
  });
  return db;
}

exports.getDb = getDb;

exports.insert = async (garbage) => {
  const categorys = category.categorys(garbage.category);
  if (categorys.length === 0) {
    return [new Error(`不合法的垃圾类型 garbage.category: ${garbage.category}`)];
  }
  if (!garbage.name) {
    return [new Error('garbage.name 不能为空')];
  }
  const db = await getDb();
  const now = new Date().toISOString();
  const result = await db.run(
    SQL`INSERT INTO Garbage (name, category, create_at, update_at) VALUES (${garbage.name}, ${garbage.category}, ${now}, ${now})`,
  ).then(r => [null, r], e => [e]);
  return result;
};

exports.find = async (garbage) => {
  if (!garbage) {
    return [new Error('名称不能为空')];
  }
  const db = await getDb();
  const result = await db.get(
    SQL`SELECT * FROM Garbage WHERE name = ${garbage}`,
  ).then(r => [null, r], e => [e]);
  return result;
};

exports.update = async (garbage) => {
  const categorys = category.categorys(garbage.category);
  if (categorys.length === 0) {
    return [new Error(`不合法的垃圾类型 garbage.category: ${garbage.category}`)];
  }
  if (!garbage.name) {
    return [new Error('garbage.name 不能为空')];
  }
  const db = await getDb();
  const now = new Date().toISOString();
  const result = await db.run(
    SQL`UPDATE Garbage SET category = ${garbage.category}, update_at = ${now} WHERE name = ${garbage.name}`,
  ).then(r => [null, r], e => [e]);
  return result;
};

exports.remove = async (garbage) => {
  if (!garbage) {
    return [new Error('名称不能为空')];
  }
  const db = await getDb();
  const result = await db.run(
    SQL`DELETE FROM Garbage WHERE name = ${garbage}`,
  ).then(r => [null, r], e => [e]);
  return result;
};
