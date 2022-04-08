import { parse, parseFile, formatters } from 'plantuml-parser';

// parse command line args
import { argv, exit } from 'process';
import * as fs from 'fs';

if (argv.length == 2) {
  console.log("This script turns the plantuml into a json.")
  console.log("Usage: node plantuml-parser.js plantuml-file")
  exit()
}

// read plantuml file
fs.readFile(argv[2], 'utf8', function (err, data) {
  if (err) throw err;

  console.log(data)

  // parse PlantUML
  const result = parse(data);

  // Format and print parse result
  console.log(
    formatters.default(result)
  );
});